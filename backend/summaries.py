"""Writes a plain-language summary of each area with Gemini, for the dashboard.

Run from the repo root with `uv run python -m backend.summaries` after
backend.functions has built data/district-needs.csv. It needs GEMINI_API_KEY in .env
and writes data/district-summaries.json, which app.py reads. The site never calls Gemini
itself: it's static, and the key must stay off the web.
"""

import json
from datetime import date

import pandas as pd
from google import genai
from google.genai import types
from pydantic import BaseModel

from backend import functions
from scripts.gemini import MODEL, client

OUTPUT = functions.ROOT / "data" / "district-summaries.json"

# The measures as the prompt describes them: (column with the share, what it means).
MEASURES = [
    ("non_english_pct", "speak a language other than English at home (age 5+)"),
    ("limited_english_pct", 'speak English less than "very well" (age 5+)'),
    ("age_65_plus_pct", "are age 65 or older"),
    ("no_internet_pct", "of households have no internet access at home"),
]

INSTRUCTIONS = """\
You write short summaries for a City of Mableton, Georgia dashboard that helps city staff
plan outreach so every resident gets city news. Readers are not technical.

Use only the numbers given. Don't invent facts about places, languages spoken, history or
causes; the data doesn't say which languages people speak. Round percentages to whole
numbers and compare with the city overall where it helps. Plain, warm, neutral language;
no jargon, no "data shows", no headings or markdown."""


class Summary(BaseModel):
    summary: str  # two or three sentences on what stands out
    ideas: list[str]  # two or three concrete outreach ideas, one sentence each


def _numbers(name: str, row: pd.Series) -> str:
    lines = [f"{name}: about {row['population']:,.0f} residents"]
    lines += [f"  {row[rate]:.1%} {meaning}" for rate, meaning in MEASURES]
    return "\n".join(lines)


def prompt(area: str, table: pd.DataFrame, city: pd.Series) -> str:
    """The data for every area (for comparison), then the one to write about."""
    context = [_numbers("All of Mableton", city)]
    context += [_numbers(f"District {d}", row) for d, row in table.iterrows()]
    return (
        "Census estimates (2020–2024) for Mableton and its six council districts:\n\n"
        + "\n\n".join(context)
        + f"\n\nWrite about {area}: a two- or three-sentence summary of what stands out "
        "for communicating with its residents, and two or three outreach ideas that fit "
        "those numbers."
    )


def summarize(
    gemini: genai.Client, area: str, table: pd.DataFrame, city: pd.Series
) -> Summary:
    response = gemini.models.generate_content(
        model=MODEL,
        contents=prompt(area, table, city),
        config=types.GenerateContentConfig(
            system_instruction=INSTRUCTIONS,
            response_mime_type="application/json",
            response_schema=Summary,
            temperature=0.3,
        ),
    )
    return response.parsed


def main():
    table = pd.read_csv(functions.OUTPUT).set_index("district")
    city = functions.city_totals(table).iloc[0]
    areas = {"city": "All of Mableton"} | {str(d): f"District {d}" for d in table.index}
    gemini = client()  # one client, kept open for every request
    summaries = {}
    for key, area in areas.items():
        print(f"Summarizing {area}...")
        summaries[key] = summarize(gemini, area, table, city).model_dump()
    OUTPUT.write_text(
        json.dumps(
            {"model": MODEL, "date": date.today().isoformat(), "areas": summaries},
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT.relative_to(functions.ROOT)}")


if __name__ == "__main__":
    main()
