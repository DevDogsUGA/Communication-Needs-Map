"""BigQuery for scripts, using the free sandbox (no billing account needed).

Sign in once with `gcloud auth application-default login` (install the gcloud CLI first:
https://cloud.google.com/sdk/docs/install). Queries run in, and count against, the team project.
"""

from google.cloud import bigquery

PROJECT = "g311-communication-needs-map"


def client() -> bigquery.Client:
    return bigquery.Client(project=PROJECT)
