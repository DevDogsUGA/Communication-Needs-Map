"""The Streamlit app. Run with `uv run streamlit run app.py`.

It reads only files committed in data/, so it needs no keys or secrets to run.
Fetching and preparing data happens in scripts/, ahead of time.
"""

import streamlit as st

st.set_page_config(page_title="Communication-needs Map", layout="wide")
st.title("Communication-needs Map")
st.write("Edit `app.py` and save; the page reloads by itself.")
