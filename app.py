"""The Streamlit app. Run with `uv run streamlit run app.py`.

It reads only files committed in data/, so it needs no keys or secrets to run.
Fetching and preparing data happens in backend/ and scripts/, ahead of time.
The pieces live in dashboard/: data.py (loading, measure wording), charts.py (figures)
and theme.py (color schemes, dark mode).
"""

import streamlit as st

from dashboard.charts import district_bars, district_map
from dashboard.data import (
    CITY,
    MEASURES,
    area_name,
    city_totals,
    in_words,
    load_boundaries,
    load_districts,
)
from dashboard.theme import SCHEMES, apply, palette

st.set_page_config(page_title="Mableton Communication Needs", layout="wide")

districts = load_districts()
boundaries = load_boundaries()
city = city_totals(districts)
AREAS = [CITY] + [area_name(d) for d in districts.index]


def pick_from_map():
    """Clicking a district on the map selects it, like the buttons above."""
    points = st.session_state["map"].selection.points
    if points and "location" in points[0]:
        st.session_state["area"] = area_name(int(points[0]["location"]))


title_column, settings_column = st.columns([3, 2], vertical_alignment="center")
with settings_column.container(
    horizontal=True,
    horizontal_alignment="right",
    vertical_alignment="center",
    gap="medium",
):
    dark = st.toggle("Dark mode", key="dark", width="content")
    scheme = st.selectbox(
        "Colors", list(SCHEMES), key="scheme", label_visibility="collapsed", width=170
    )
p = palette(dark, scheme)
apply(p)

title_column.title("Mableton Communication Needs")
st.markdown(
    "Who might miss city news, and why? This shows where residents speak "
    "other languages, are 65 or older, or have no internet at home, so outreach "
    "can reach everyone."
)

area = st.segmented_control(
    "Show numbers for", AREAS, default=CITY, required=True, key="area"
)
selected = None if area == CITY else int(area.removeprefix("District "))
row = city if selected is None else districts.loc[selected]

# --- Headline numbers for the chosen area -------------------------------------------
st.header(area, divider=p.divider)
st.markdown(
    f"About **{row['population']:,.0f}** residents and **{row['households']:,.0f}** "
    "households."
)

for column, m in zip(st.columns(len(MEASURES)), MEASURES):
    with column.container(border=True, height="stretch"):
        delta = None
        if selected is not None:
            points = (row[m.rate] - city[m.rate]) * 100
            delta = f"{points:+.1f} points vs. all of Mableton"
        st.markdown(f"**{m.title}**")
        st.metric(
            m.title,
            f"{row[m.rate]:.1%}",
            delta,
            delta_color="off",
            label_visibility="collapsed",
        )
        st.markdown(
            f"{in_words(row[m.rate]).capitalize()} {m.base_label} {m.sentence} "
            f"({row[m.count]:,.0f} of {row[m.base]:,.0f})."
        )
        st.caption(f"Why it matters: {m.why}")

# --- Compare the districts ----------------------------------------------------------
st.header("Compare the districts", divider=p.divider)
short = st.segmented_control(
    "Measure",
    [m.short for m in MEASURES],
    default=MEASURES[0].short,
    required=True,
    key="measure",
)
measure = next(m for m in MEASURES if m.short == short)

rates = districts[measure.rate]
st.markdown(
    f"**{measure.title}:** highest in **District {rates.idxmax()}** "
    f"({rates.max():.1%}), lowest in **District {rates.idxmin()}** ({rates.min():.1%}). "
    f"Across Mableton it's {city[measure.rate]:.1%}."
)

map_column, bar_column = st.columns([3, 2], gap="large")
with map_column:
    st.plotly_chart(
        district_map(districts, boundaries, measure, selected, p),
        key="map",
        on_select=pick_from_map,
        selection_mode="points",
        theme=None,
        config={"displayModeBar": False, "scrollZoom": False},
    )
    shade = "Brighter" if p.dark else "Darker"
    st.caption(
        f"{shade} districts have a higher share. Point at a district for details."
    )
with bar_column:
    st.plotly_chart(
        district_bars(districts, city[measure.rate], measure, selected, p),
        theme=None,
        config={"displayModeBar": False},
    )

# --- Details --------------------------------------------------------------------------
with st.expander("See all the numbers"):
    table = districts.copy()
    table.loc[CITY] = city
    table.index = [area_name(d) if d != CITY else CITY for d in table.index]
    columns = {"population": "Residents", "households": "Households"}
    for m in MEASURES:
        columns[m.rate] = f"{m.short} (%)"
        columns[m.count] = f"{m.short} (count)"
    table = table[list(columns)].rename(columns=columns)
    st.dataframe(
        table.style.format(
            {c: "{:.1%}" if c.endswith("(%)") else "{:,.0f}" for c in table.columns}
        ),
        width="stretch",
    )

with st.expander("Where these numbers come from"):
    st.markdown(
        """
- **Source:** U.S. Census Bureau, American Community Survey 5-year estimates
  (2020–2024). The survey asks a sample of homes, so every number is an estimate.
- **Districts:** the Census doesn't report by council district. Its small areas
  (block groups) were split across districts by land area, which assumes people
  are spread evenly within each one, so a district's totals can be off by up to
  about 10%.
- **Language** counts residents age 5 and over. "Less than very well" is how
  people described their own English.
- **No internet** means a household has no internet access at all, including
  cell phone data.
"""
    )
