"""Turns Census block group data into one row per Mableton council district.

Run from the repo root with `uv run python -m backend.functions`. It writes
data/district-needs.csv, which app.py can read (see data/README.md for the columns).

Block groups don't follow district lines, so each block group's counts are split across the
districts it overlaps in proportion to the share of its area inside each one (areal
weighting). That assumes people are spread evenly within a block group.
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd

from backend import census

ROOT = Path(__file__).parent.parent
DISTRICTS = ROOT / "data" / "mableton-council-districts.geojson"
OUTPUT = ROOT / "data" / "district-needs.csv"
# UTM zone 16N, in meters, for measuring areas around Mableton
EQUAL_AREA = "EPSG:26916"


def lines(table: str, numbers) -> list[str]:
    return [f"{table}_{n:03d}E" for n in numbers]


# B16004 lists, for each age group (5-17, 18-64, 65+), each non-English language followed by
# four lines on how well its speakers speak English: "very well", "well", "not well",
# "not at all". Limited English (the Census definition) is anything below "very well".
LANGUAGES = [4, 9, 14, 19, 26, 31, 36, 41, 48, 53, 58, 63]
LIMITED_ENGLISH = [n + k for n in LANGUAGES for k in (2, 3, 4)]

# Each count is the sum of these ACS variables.
COUNTS = {
    # B01001 Sex by age
    "population": lines("B01001", [1]),
    "age_65_plus": lines("B01001", [*range(20, 26), *range(44, 50)]),
    # B16004 Age by language spoken at home by ability to speak English (ages 5 and up)
    "population_5_plus": lines("B16004", [1]),
    "speak_only_english": lines("B16004", [3, 25, 47]),
    "limited_english": lines("B16004", LIMITED_ENGLISH),
    # B28002 Presence and types of internet subscriptions in household
    "households": lines("B28002", [1]),
    "households_no_internet": lines("B28002", [13]),
}

# Shares to compute after summing: name -> (numerator, denominator).
RATES = {
    "non_english_pct": ("non_english", "population_5_plus"),
    "limited_english_pct": ("limited_english", "population_5_plus"),
    "age_65_plus_pct": ("age_65_plus", "population"),
    "no_internet_pct": ("households_no_internet", "households"),
}


def block_group_counts(estimates: pd.DataFrame) -> pd.DataFrame:
    """Sums the ACS variables in COUNTS, one row per block group."""
    return pd.DataFrame(
        {name: estimates[variables].sum(axis=1) for name, variables in COUNTS.items()}
    )


def district_weights(
    shapes: gpd.GeoDataFrame, districts: gpd.GeoDataFrame
) -> pd.DataFrame:
    """For each block group and district they share: the share of the block group's area
    inside that district. Columns GEOID, district, weight."""
    shapes = shapes.to_crs(EQUAL_AREA)
    shapes["bg_area"] = shapes.area
    pieces = gpd.overlay(
        shapes,
        districts[["district", "geometry"]].to_crs(EQUAL_AREA),
        how="intersection",
    )
    pieces["weight"] = pieces.area / pieces["bg_area"]
    return pd.DataFrame(pieces[["GEOID", "district", "weight"]])


def apportion(counts: pd.DataFrame, weights: pd.DataFrame) -> pd.DataFrame:
    """Splits block group counts across districts by weight and sums them per district."""
    joined = weights.join(counts, on="GEOID")
    weighted = joined[counts.columns].mul(joined["weight"], axis=0)
    return weighted.groupby(joined["district"]).sum().sort_index()


def add_rates(districts: pd.DataFrame) -> pd.DataFrame:
    """Adds the derived counts and the shares in RATES (0 to 1)."""
    out = districts.copy()
    out["non_english"] = out["population_5_plus"] - out["speak_only_english"]
    for name, (numerator, denominator) in RATES.items():
        out[name] = out[numerator] / out[denominator]
    return out


def city_totals(table: pd.DataFrame) -> pd.DataFrame:
    """All six districts together, as one row: summed counts, with shares recomputed."""
    totals = add_rates(table[list(COUNTS)].sum().to_frame().T)
    totals[list(RATES)] = totals[list(RATES)].round(4)
    return totals


def build() -> pd.DataFrame:
    """Fetches everything and returns one row per district: counts, then shares."""
    estimates = census.acs_block_groups(
        sorted({v for vs in COUNTS.values() for v in vs})
    )
    districts = gpd.read_file(DISTRICTS)
    weights = district_weights(census.block_group_shapes(), districts)
    table = add_rates(apportion(block_group_counts(estimates), weights))
    counts = [c for c in table.columns if c not in RATES]
    table[counts] = table[counts].round().astype(int)
    table[list(RATES)] = table[list(RATES)].round(4)
    return table.reset_index()


def main():
    table = build()
    table.to_csv(OUTPUT, index=False)
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    # Sanity check: the areal estimate should land near each district's 2020 Census count.
    census_2020 = gpd.read_file(DISTRICTS).set_index("district")["population"]
    check = table.set_index("district")[["population"]].join(census_2020.rename("2020"))
    print(check.to_string())


if __name__ == "__main__":
    main()
