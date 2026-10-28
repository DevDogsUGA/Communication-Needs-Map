"""Fetches the raw inputs: ACS 5-year estimates and block group shapes for Cobb County.

Used by backend/functions.py, which runs the whole pipeline. The web API is backend/api.py.
"""

import io

import geopandas as gpd
import pandas as pd
import requests

from scripts.census_api import COUNTY, STATE, get

ACS = "2024/acs/acs5"
TIGER = "https://www2.census.gov/geo/tiger/TIGER2024/BG/tl_2024_{state}_bg.zip"
GEOGRAPHY = ["state", "county", "tract", "block group"]
MAX_VARIABLES = 49  # the API allows 50 per call, including the geography


def acs_block_groups(variables: list[str]) -> pd.DataFrame:
    """ACS estimates for every Cobb County block group, indexed by the 12-digit GEOID."""
    frames = []
    for i in range(0, len(variables), MAX_VARIABLES):
        chunk = variables[i : i + MAX_VARIABLES]
        df = get(ACS, chunk, "block group:*", f"state:{STATE} county:{COUNTY}")
        df.index = df[GEOGRAPHY].agg("".join, axis=1).rename("GEOID")
        frames.append(df[chunk])
    estimates = pd.concat(frames, axis=1).apply(pd.to_numeric)
    # Negative values are the API's codes for missing estimates (e.g. -666666666).
    return estimates.mask(estimates < 0)


def block_group_shapes() -> gpd.GeoDataFrame:
    """TIGER/Line block group boundaries for Cobb County, with a GEOID column."""
    response = requests.get(TIGER.format(state=STATE), timeout=300)
    response.raise_for_status()
    shapes = gpd.read_file(io.BytesIO(response.content), where=f"COUNTYFP='{COUNTY}'")
    return shapes[["GEOID", "geometry"]]
