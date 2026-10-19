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

### Census data: BigQuery sandbox

`scripts/bigquery.py` has `client()`, a [BigQuery](https://cloud.google.com/bigquery/docs/sandbox) client for the team project. Google hosts Census data as [public datasets](https://console.cloud.google.com/marketplace/browse?filter=solution-type:dataset&q=census), for example `bigquery-public-data.census_bureau_acs` (American Community Survey) and `bigquery-public-data.geo_census_blockgroups` (block group shapes). Check which survey year a table covers before you use it; some are several years old.

Sign in once: install the [gcloud CLI](https://cloud.google.com/sdk/docs/install), then run `gcloud auth application-default login` with the Google account you gave on the team form.

```python
from bigquery import client

df = (
    client()
    .query("SELECT ... FROM `bigquery-public-data.census_bureau_acs....`")
    .to_dataframe()
)
```

The sandbox is free with limits (10 GB storage, 1 TB of queries a month) and tables expire after 60 days, so save results to `data/`.

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

[Streamlit Community Cloud](https://streamlit.io/cloud) is free and runs straight from this repo: sign in with GitHub, choose **Create app**, pick this repo, branch `main` and file `app.py`. It redeploys on every push to `main`. Apps sleep after 12 hours without visitors and wake on the next visit.
