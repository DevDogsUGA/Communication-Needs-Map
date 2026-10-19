# Data

Files here are committed and read by `app.py`.

- `mableton-council-districts.geojson`: the six council districts. Properties: `district` (1–6) and `population` (2020 Census).
- `mableton-city-limits.geojson`: the city boundary.

Both come from the public layer the city's [Find My District](https://www.mableton.gov/1247/Find-My-District) lookup uses: <https://services5.arcgis.com/Mm1BAVEiAXrYE9vn/arcgis/rest/services/CouncilDistricts_CityLimits/FeatureServer> (layers 2 and 3), converted to WGS 84 (EPSG:4326).
