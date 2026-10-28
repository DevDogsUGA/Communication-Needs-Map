"""A FastAPI server for the district communication-needs data.

Run from the repo root with `uv run uvicorn backend.api:app --reload`, then open
http://localhost:8000/docs for the interactive docs.

It serves data/district-needs.csv, which backend/functions.py builds from the Census API.
POST /refresh rebuilds that file (it needs CENSUS_API_KEY in .env and takes a minute or so).
"""

import json

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend import functions

app = FastAPI(
    title="Mableton communication needs",
    description="Census measures of language, age 65+ and internet access by council district.",
)
# The data is public, so any frontend (including one running in the browser) may read it.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"])


def load() -> pd.DataFrame:
    if not functions.OUTPUT.exists():
        raise HTTPException(503, "No data yet: POST /refresh to build it.")
    return pd.read_csv(functions.OUTPUT)


def records(df: pd.DataFrame) -> list[dict]:
    # Through JSON so numpy numbers become plain ints and floats.
    return json.loads(df.to_json(orient="records"))


@app.get("/districts")
def districts() -> list[dict]:
    """Every measure for each of the six council districts."""
    return records(load())


@app.get("/districts/geojson")
def districts_geojson() -> dict:
    """The district boundaries, with every measure added to each district's properties."""
    by_district = load().set_index("district")
    geojson = json.loads(functions.DISTRICTS.read_text())
    for feature in geojson["features"]:
        district = feature["properties"]["district"]
        measures = records(by_district.loc[[district]].reset_index())[0]
        feature["properties"] = {
            **feature["properties"],
            **measures,
            "census_2020_population": feature["properties"]["population"],
        }
    return geojson


@app.get("/districts/{district}")
def district(district: int) -> dict:
    """Every measure for one district (1–6)."""
    rows = load().query("district == @district")
    if rows.empty:
        raise HTTPException(404, f"No district {district}; districts are 1–6.")
    return records(rows)[0]


@app.get("/summary")
def summary() -> dict:
    """All of Mableton: the six districts' counts summed, with shares recomputed."""
    return records(functions.city_totals(load()))[0]


@app.post("/refresh")
def refresh() -> dict:
    """Fetches fresh Census data and rebuilds data/district-needs.csv."""
    table = functions.build()
    table.to_csv(functions.OUTPUT, index=False)
    return {"districts": len(table), "file": str(functions.OUTPUT.name)}
