from fastapi.testclient import TestClient

from backend.api import app

client = TestClient(app)


def test_districts():
    rows = client.get("/districts").json()
    assert [row["district"] for row in rows] == [1, 2, 3, 4, 5, 6]


def test_one_district():
    assert client.get("/districts/3").json()["district"] == 3
    assert client.get("/districts/7").status_code == 404


def test_summary_adds_up():
    rows = client.get("/districts").json()
    summary = client.get("/summary").json()
    assert summary["population"] == sum(row["population"] for row in rows)
    assert 0 <= summary["non_english_pct"] <= 1


def test_geojson_has_measures():
    feature = client.get("/districts/geojson").json()["features"][0]
    assert {"district", "no_internet_pct", "census_2020_population"} <= set(
        feature["properties"]
    )
