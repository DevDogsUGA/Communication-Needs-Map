# Data

Files here are committed and read by `app.py`.

- `mableton-council-districts.geojson`: the six council districts. Properties: `district` (1–6) and `population` (2020 Census).
- `mableton-city-limits.geojson`: the city boundary.
- `district-needs.csv`: communication-needs measures for each district, built by `uv run python -m backend.functions` (see below).

The two GeoJSON files come from the public layer the city's [Find My District](https://www.mableton.gov/1247/Find-My-District) lookup uses: <https://services5.arcgis.com/Mm1BAVEiAXrYE9vn/arcgis/rest/services/CouncilDistricts_CityLimits/FeatureServer> (layers 2 and 3), converted to WGS 84 (EPSG:4326).

## district-needs.csv

One row per council district (`district`, 1–6, joins to the GeoJSON). Source: ACS 2020–2024 5-year estimates (`2024/acs/acs5`) for Cobb County block groups. Block groups are split across the districts they overlap by share of area, so the numbers are estimates and won't exactly match the 2020 `population` in the GeoJSON.

Counts (people unless noted):

| Column | Meaning | ACS |
| --- | --- | --- |
| `population` | Total population | B01001_001 |
| `age_65_plus` | Age 65 and over | B01001 |
| `population_5_plus` | Age 5 and over (the universe for language) | B16004_001 |
| `speak_only_english` | Speak only English at home | B16004 |
| `non_english` | Speak a language other than English at home | B16004 |
| `limited_english` | Speak English less than "very well" | B16004 |
| `households` | Households | B28002_001 |
| `households_no_internet` | Households with no internet access at all | B28002_013 |

Shares (0 to 1): `non_english_pct` and `limited_english_pct` (of `population_5_plus`), `age_65_plus_pct` (of `population`), `no_internet_pct` (of `households`).
