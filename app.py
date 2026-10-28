"""Mableton communication-needs frontend. Run: uv run streamlit run app.py.

Boundary polygons and 2020 population come from committed data/ GeoJSON.
Demographic rates are DEMONSTRATION ONLY until a validated CSV is supplied.
"""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import pydeck as pdk
import streamlit as st

BASE = Path(__file__).resolve().parent
BOUNDARIES = BASE / "data" / "mableton-council-districts.geojson"
METRICS_CSV = BASE / "data" / "district_metrics.csv"
METRICS = {
    "Language other than English at home": "language_pct",
    "Residents age 65+": "age65_pct",
    "Households without internet": "no_internet_pct",
}
COLORS = {
    "Language other than English at home": "#6366f1",
    "Residents age 65+": "#0891b2",
    "Households without internet": "#e07a39",
}

st.set_page_config(
    page_title="Mableton | Communication Needs", page_icon="🗺️", layout="wide"
)
st.markdown(
    """<style>
.block-container {padding-top: 1.4rem; max-width: 1320px;}
[data-testid="stMetric"] {background: #f3f6fa; padding: 16px; border-radius: 12px; border: 1px solid #e2e8f0;}
[data-testid="stMetricLabel"] {color: #334155;}
</style>""",
    unsafe_allow_html=True,
)


@st.cache_data
def load_boundaries():
    with BOUNDARIES.open(encoding="utf-8") as f:
        geo = json.load(f)
    features = geo.get("features", [])
    if len(features) != 6:
        raise ValueError("Expected six council district polygons")
    rows = []
    for feature in features:
        props = feature["properties"]
        number = int(props["district"])
        rows.append({"district": number, "population": int(props["population"])})
    return geo, pd.DataFrame(rows).sort_values("district").reset_index(drop=True)


def polygon_center(feature):
    """Area-weighted polygon-ring centroid for 3D column positioning."""
    geometry = feature["geometry"]
    polygon = (
        geometry["coordinates"][0]
        if geometry["type"] == "Polygon"
        else geometry["coordinates"][0][0]
    )
    twice_area = 0.0
    sx = sy = 0.0
    for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1]):
        cross = x1 * y2 - x2 * y1
        twice_area += cross
        sx += (x1 + x2) * cross
        sy += (y1 + y2) * cross
    if abs(twice_area) > 1e-12:
        return sx / (3 * twice_area), sy / (3 * twice_area)
    return (
        sum(p[0] for p in polygon) / len(polygon),
        sum(p[1] for p in polygon) / len(polygon),
    )


def load_metrics():
    if METRICS_CSV.exists():
        frame = pd.read_csv(METRICS_CSV)
        required = ["district", *METRICS.values()]
        missing = [name for name in required if name not in frame.columns]
        if missing:
            st.error("district_metrics.csv is missing columns: " + ", ".join(missing))
            st.stop()
        frame = frame[required].copy()
        for name in required:
            frame[name] = pd.to_numeric(frame[name], errors="coerce")
        if frame[required].isna().any().any() or frame["district"].duplicated().any():
            st.error("CSV has missing, nonnumeric, or duplicate district values.")
            st.stop()
        if not frame["district"].between(1, 6).all() or set(frame["district"]) != set(
            range(1, 7)
        ):
            st.error("CSV must contain exactly one row for each district, 1 through 6.")
            st.stop()
        if not all(frame[c].between(0, 100).all() for c in METRICS.values()):
            st.error("Demographic percentages must be between 0 and 100.")
            st.stop()
        return frame, False
    # Fictional values ONLY to demonstrate the interface. Not Census estimates.
    return pd.DataFrame(
        {
            "district": [1, 2, 3, 4, 5, 6],
            "language_pct": [31, 22, 27, 18, 25, 34],
            "age65_pct": [15, 19, 24, 21, 17, 13],
            "no_internet_pct": [12, 16, 11, 20, 18, 14],
        }
    ), True


try:
    geojson, population = load_boundaries()
except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
    st.error(f"Cannot read the official district boundary file: {exc}")
    st.stop()

rates, demo_mode = load_metrics()
df = population.merge(rates, on="district", how="left", validate="one_to_one")
if df[list(METRICS.values())].isna().any().any():
    st.error("Some districts are missing demographic data")
    st.stop()

st.sidebar.markdown("### Map controls")
district = st.sidebar.selectbox(
    "Council district", df["district"].tolist(), format_func=lambda x: f"District {x}"
)
metric_label = st.sidebar.radio("Color / column height", list(METRICS))
map_style = st.sidebar.radio(
    "Map display", ["District boundaries", "3D columns"], horizontal=False
)
metric = METRICS[metric_label]
selected = df.loc[df["district"] == district].iloc[0]

st.title("Mableton Communication-needs Map")
st.caption(
    "Georgia 311 Challenge · Reach Every Resident · Six Mableton council districts"
)
if demo_mode:
    st.warning(
        "DEMO DATA: Language, age 65+, and internet percentages are fictional placeholders. The district shapes and 2020 populations are real. Add data/district_metrics.csv to use prepared statistics."
    )
else:
    st.info(
        "Showing the team's prepared district_metrics.csv. Verify data source, year, denominator, and district aggregation before presenting figures as official."
    )

st.subheader(f"District {district} overview")
a, b, c, d = st.columns(4)
a.metric("2020 population", f"{int(selected['population']):,}")
b.metric("Other language at home", f"{selected['language_pct']:.1f}%")
c.metric("Age 65+", f"{selected['age65_pct']:.1f}%")
d.metric("No internet", f"{selected['no_internet_pct']:.1f}%")

st.subheader("District map")
st.caption(
    "Choose a district in the sidebar. Hover over a district or column to inspect its information."
)

# Attach all three metrics to each official district polygon, enabling tooltips.
for feature in geojson["features"]:
    props = feature["properties"]
    num = int(props["district"])
    item = df.loc[df["district"] == num].iloc[0]
    props.update(
        {
            "district_name": f"District {num}",
            "language_pct": float(item["language_pct"]),
            "age65_pct": float(item["age65_pct"]),
            "no_internet_pct": float(item["no_internet_pct"]),
            "metric_value": float(item[metric]),
            "fill_color": [37, 99, 235, 185]
            if num == district
            else [99, 102, 241, 65 + int(item[metric] * 3)],
        }
    )

# Map uses official GeoJSON geometry rather than approximate district markers.
polygon_layer = pdk.Layer(
    "GeoJsonLayer",
    data=geojson,
    pickable=True,
    auto_highlight=True,
    filled=True,
    stroked=True,
    get_fill_color="properties.fill_color",
    get_line_color=[255, 255, 255, 220],
    get_line_width=120,
    line_width_min_pixels=2,
)

layers = [polygon_layer]
if map_style == "3D columns":
    column_rows = []
    for feature in geojson["features"]:
        props = feature["properties"]
        lng, lat = polygon_center(feature)
        column_rows.append(
            {
                "district": int(props["district"]),
                "lng": lng,
                "lat": lat,
                "population": int(props["population"]),
                "language_pct": props["language_pct"],
                "age65_pct": props["age65_pct"],
                "no_internet_pct": props["no_internet_pct"],
                "metric_value": props["metric_value"],
                "fill_color": [37, 99, 235, 230]
                if props["district"] == district
                else [224, 122, 57, 190],
            }
        )
    layers.append(
        pdk.Layer(
            "ColumnLayer",
            data=pd.DataFrame(column_rows),
            get_position="[lng, lat]",
            get_elevation="metric_value",
            elevation_scale=130,
            radius=430,
            get_fill_color="fill_color",
            pickable=True,
            auto_highlight=True,
            extruded=True,
        )
    )

view = pdk.ViewState(
    latitude=33.82,
    longitude=-84.57,
    zoom=10.8,
    pitch=52 if map_style == "3D columns" else 0,
    bearing=20 if map_style == "3D columns" else 0,
)
tooltip = {
    "html": "<b>District {district}</b><br/>Other language: {language_pct}%<br/>Age 65+: {age65_pct}%<br/>No internet: {no_internet_pct}%<br/>2020 population: {population}",
    "style": {"backgroundColor": "#172033", "color": "white"},
}
st.pydeck_chart(
    pdk.Deck(
        layers=layers,
        initial_view_state=view,
        tooltip=tooltip,
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    ),
    width="stretch",
    height=490,
)

left, right = st.columns([1.1, 1])
with left:
    st.subheader("Compare all districts")
    chart = px.bar(
        df,
        x="district",
        y=metric,
        text_auto=".1f",
        labels={"district": "Council district", metric: "Percent (%)"},
        color_discrete_sequence=[COLORS[metric_label]],
    )
    chart.update_layout(
        yaxis_range=[0, 100], showlegend=False, margin={"l": 0, "r": 0, "t": 10, "b": 0}
    )
    st.plotly_chart(chart, width="stretch")
with right:
    st.subheader(f"District {district}: three measures")
    breakdown = pd.DataFrame(
        {
            "Measure": list(METRICS),
            "Percent": [float(selected[col]) for col in METRICS.values()],
        }
    )
    fig = px.bar(
        breakdown,
        x="Percent",
        y="Measure",
        orientation="h",
        text_auto=".1f",
        color="Measure",
        color_discrete_map=COLORS,
    )
    fig.update_layout(
        xaxis_range=[0, 100], showlegend=False, margin={"l": 0, "r": 0, "t": 10, "b": 0}
    )
    st.plotly_chart(fig, width="stretch")

st.subheader("Possible outreach considerations")
notes = []
if selected["language_pct"] >= 30:
    notes.append(
        "Explore multilingual notices and partnerships with trusted community organizations."
    )
if selected["age65_pct"] >= 20:
    notes.append(
        "Consider accessible print materials and outreach through senior/community centers."
    )
if selected["no_internet_pct"] >= 18:
    notes.append(
        "Include offline options such as mailed notices, flyers, and in-person announcements."
    )
if not notes:
    notes.append(
        "Consider combining digital updates with community partnerships and accessible print notices."
    )
for note in notes:
    st.write("• " + note)
st.caption(
    "These are illustrative suggestions, not measured outreach preferences. Thresholds are design rules, not research findings."
)

st.subheader("District data")
st.dataframe(
    df.rename(
        columns={
            "district": "District",
            "population": "2020 population",
            "language_pct": "Other language (%)",
            "age65_pct": "Age 65+ (%)",
            "no_internet_pct": "No internet (%)",
        }
    ),
    hide_index=True,
    width="stretch",
)
st.download_button(
    "Download displayed data (CSV)",
    data=df.to_csv(index=False),
    file_name="mableton_district_dashboard_data.csv",
    mime="text/csv",
)
st.caption(
    "Boundary and 2020 population source: Mableton council district GeoJSON committed in the team's data/ directory."
)
