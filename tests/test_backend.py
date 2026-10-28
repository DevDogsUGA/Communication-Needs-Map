import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from backend.functions import EQUAL_AREA, apportion, district_weights


def test_block_group_split_by_area():
    # One block group straddles two districts, 3/4 in district 1 and 1/4 in district 2.
    shapes = gpd.GeoDataFrame(
        {"GEOID": ["a", "b"]},
        geometry=[box(0, 0, 4, 1), box(4, 0, 5, 1)],
        crs=EQUAL_AREA,
    )
    districts = gpd.GeoDataFrame(
        {"district": [1, 2]},
        geometry=[box(0, 0, 3, 1), box(3, 0, 5, 1)],
        crs=EQUAL_AREA,
    )
    counts = pd.DataFrame({"population": [400, 100]}, index=pd.Index(["a", "b"]))

    result = apportion(counts, district_weights(shapes, districts))

    assert result.loc[1, "population"] == 300
    assert result.loc[2, "population"] == 200


def test_district_needs_has_six_districts():
    table = pd.read_csv("data/district-needs.csv")
    assert sorted(table["district"]) == [1, 2, 3, 4, 5, 6]
