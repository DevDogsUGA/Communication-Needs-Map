"""The Census Data API (https://www.census.gov/data/developers.html).

It needs a key: get a free one at https://api.census.gov/data/key_signup.html (it arrives by
email in a few minutes) and put it in .env as CENSUS_API_KEY.
Find variables at https://api.census.gov/data/2024/acs/acs5/variables.html.
"""

import os

import pandas as pd
import requests
from dotenv import load_dotenv

# Cobb County, Georgia
STATE = "13"
COUNTY = "067"


def get(
    dataset: str, variables: list[str], geography: str, within: str
) -> pd.DataFrame:
    """One API call as a DataFrame.

    Example: get("2024/acs/acs5", ["B01001_001E"], "block group:*", f"state:{STATE} county:{COUNTY}")
    """
    load_dotenv()
    key = os.environ.get("CENSUS_API_KEY")
    if not key:
        raise SystemExit(
            "Set CENSUS_API_KEY in .env (free key: https://api.census.gov/data/key_signup.html)"
        )
    params = {"get": ",".join(variables), "for": geography, "in": within, "key": key}
    response = requests.get(
        f"https://api.census.gov/data/{dataset}", params=params, timeout=60
    )
    response.raise_for_status()
    header, *rows = response.json()
    return pd.DataFrame(rows, columns=header)
