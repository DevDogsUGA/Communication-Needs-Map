"""Loads the committed data and describes each measure in plain language."""

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

DATA = Path(__file__).parent.parent / "data"
CITY = "All of Mableton"


@dataclass(frozen=True)
class Measure:
    title: str  # what the share means, as a heading
    short: str  # a few words, for buttons and axis titles
    count: str  # column with the number of people or homes
    base: str  # column with the number it's a share of
    base_label: str  # what `base` counts, in words
    rate: str  # column with the share, 0 to 1
    sentence: str  # finishes "About 3 in 10 residents ..."
    why: str  # why it matters for reaching residents


MEASURES = [
    Measure(
        title="Speak a language other than English at home",
        short="Other language at home",
        count="non_english",
        base="population_5_plus",
        base_label="residents age 5 and over",
        rate="non_english_pct",
        sentence="speak a language other than English at home",
        why="City news may need to go out in more than one language.",
    ),
    Measure(
        title="Speak English less than “very well”",
        short="Limited English",
        count="limited_english",
        base="population_5_plus",
        base_label="residents age 5 and over",
        rate="limited_english_pct",
        sentence="speak English less than “very well”",
        why="These residents may need translated materials or an interpreter.",
    ),
    Measure(
        title="Age 65 and over",
        short="Age 65+",
        count="age_65_plus",
        base="population",
        base_label="residents",
        rate="age_65_plus_pct",
        sentence="are age 65 or older",
        why="Older residents often rely on mail, phone calls and in-person events.",
    ),
    Measure(
        title="Homes with no internet access",
        short="No internet at home",
        count="households_no_internet",
        base="households",
        base_label="households",
        rate="no_internet_pct",
        sentence="have no internet access at home",
        why="These homes won't see website or social media posts.",
    ),
]

COUNTS = [
    "population",
    "population_5_plus",
    "households",
    *dict.fromkeys(m.count for m in MEASURES),
]


def load_districts() -> pd.DataFrame:
    """One row per district (1–6), from data/district-needs.csv."""
    return pd.read_csv(DATA / "district-needs.csv").set_index("district")


def city_totals(districts: pd.DataFrame) -> pd.Series:
    """All six districts together: summed counts, with shares recomputed from them."""
    totals = districts[COUNTS].sum()
    for m in MEASURES:
        totals[m.rate] = totals[m.count] / totals[m.base]
    return totals


def load_boundaries() -> dict:
    return json.loads(
        (DATA / "mableton-council-districts.geojson").read_text(encoding="utf-8")
    )


def area_name(district: int | None) -> str:
    return CITY if district is None else f"District {district}"


def in_words(share: float) -> str:
    """A share as a phrase people can picture, like "about 3 in 10" or "about 4 in 100"."""
    if share >= 0.095:
        return f"about {round(share * 10)} in 10"
    return f"about {max(round(share * 100), 1)} in 100"
