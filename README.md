# Communication-needs Map

Georgia 311 Challenge 2026 · DevDogs (GDG on Campus UGA)

- Track: Reach Every Resident
- Advisor: Kyle Quach and Shakthi Karthik
- Sprint: Oct 16–30, 2026. Demo Day: Fri Oct 30 at DevFest Atlanta.

## What's here

A blank [Streamlit](https://streamlit.io) app, plus the council district boundaries. Nothing is built yet; that's up to you.

| File | What it's for |
| --- | --- |
| `app.py` | The app. Start here. It should read only files in `data/`, so it runs anywhere with no keys. |
| `data/` | Committed data the app reads. The six council districts and the city limits are already here (see `data/README.md` for the source). |
| `scripts/` | Code you run on your own machine to fetch and prepare data, writing the results to `data/`. [geopandas](https://geopandas.org) is installed for joining Census areas to districts. |
| `scripts/gemini.py` | `client()` returns a Gemini client for writing summaries ahead of time. It reads `GEMINI_API_KEY` from `.env` (copy `.env.example`). |
| `tests/` | [pytest](https://docs.pytest.org) tests. `test_app.py` checks the app starts without errors. |

### Census data: Census API

`scripts/census_api.py` has `get()`, which makes one [Census Data API](https://www.census.gov/data/developers.html) call and returns a DataFrame. The API has the newest [American Community Survey](https://www.census.gov/programs-surveys/acs) 5-year estimates. Block group shapes to join with come from [TIGER/Line](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html).

```python
from census_api import COUNTY, STATE, get

df = get(
    "2024/acs/acs5", ["B01001_001E"], "block group:*", f"state:{STATE} county:{COUNTY}"
)
```

The API needs a key. Get a [free key](https://api.census.gov/data/key_signup.html) (it comes by email within minutes) and put it in `.env` as `CENSUS_API_KEY`.
If Gemini replies "This model is currently experiencing high demand", change the model in `scripts/gemini.py` to an older Flash model such as `gemini-3.5-flash`. The newest model is the busiest on the free tier.

### Backend: district measures and FastAPI

`backend/` fetches ACS block group data for language spoken at home, age 65+ and internet access, splits it across the six council districts by area, and writes `data/district-needs.csv` (columns in `data/README.md`).

```sh
uv run python -m backend.functions          # rebuild data/district-needs.csv (needs CENSUS_API_KEY)
uv run python -m backend.summaries         # rewrite data/district-summaries.json with Gemini (needs GEMINI_API_KEY)
uv run uvicorn backend.api:app --reload     # serve it at http://localhost:8000 (docs at /docs)
```

Endpoints: `GET /districts`, `GET /districts/{n}`, `GET /districts/geojson` (boundaries with measures), `GET /summary` (city-wide), `POST /refresh` (rebuild from the Census API).

The Census data source comes in a separate pull request: the BigQuery sandbox or the Census API. Merge one.

## Run it locally

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```sh
uv sync
uv run streamlit run app.py        # http://localhost:8501, reloads as you edit
uv run python scripts/<script>.py  # run a data script
```

Before you push:

```sh
uv run ruff format    # formats
uv run ruff check     # lint (CI runs this)
uv run pytest         # tests (CI runs this)
```

Add packages with `uv add <package>` (the app needs it) or `uv add --group dev <package>` (only scripts or tests need it). After `uv add`, refresh `requirements.txt`, which Streamlit Community Cloud installs from:

```sh
uv export --no-dev --no-hashes --no-emit-project -o requirements.txt
```

## Deploy

### Firebase Hosting (stlite)

The same `app.py` also runs entirely in the visitor's browser with [stlite](https://github.com/whitphx/stlite), served from Firebase Hosting:

- **Every pull request** gets a preview link, posted as a comment on the PR.
- **Merging to `main`** deploys https://g311-communication-needs-map.web.app

`scripts/build_site.py` builds it into `site/`. To try it locally:

```sh
uv run python scripts/build_site.py
uv run python -m http.server -d site    # http://localhost:8000
```

Trade-offs: the first load takes 10 to 30 seconds while Python downloads into the browser, and only pure-Python packages or ones [Pyodide supports](https://pyodide.org/en/stable/usage/packages-in-pyodide.html) work. Keep heavy work (geopandas, API calls) in `scripts/` and commit the results to `data/`.

### Streamlit Community Cloud

[Streamlit Community Cloud](https://streamlit.io/cloud) is free and runs straight from this repo: sign in with GitHub, choose **Create app**, pick this repo, branch `main` and file `app.py`. It redeploys on every push to `main`. Apps sleep after 12 hours without visitors and wake on the next visit.
