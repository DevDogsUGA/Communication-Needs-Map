"""The map and the district comparison chart (Plotly figures)."""

import itertools

import pandas as pd
import plotly.graph_objects as go

from dashboard.data import Measure

# One blue, light to dark: more of the measure is darker.
BLUES = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95"]
ACCENT = "#2a78d6"
MUTED = "#c3c2b7"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e1e0d9"
FONT = {"family": 'system-ui, -apple-system, "Segoe UI", sans-serif', "color": INK}


def _hover(measure: Measure) -> str:
    return (
        "<b>%{customdata[0]}</b><br>"
        f"{measure.title}: <b>%{{customdata[1]:.1%}}</b><br>"
        f"%{{customdata[2]:,}} of %{{customdata[3]:,}} {measure.base_label}"
        "<extra></extra>"
    )


def _customdata(districts: pd.DataFrame, measure: Measure) -> list:
    return [
        [f"District {d}", row[measure.rate], row[measure.count], row[measure.base]]
        for d, row in districts.iterrows()
    ]


def _percent_format(rates: pd.Series) -> str:
    """Whole percents, or one decimal when the range is too narrow to tell ticks apart."""
    return ".1%" if rates.max() - rates.min() < 0.05 else ".0%"


def _rings(geometry: dict) -> list:
    """The outer boundary of each polygon in a GeoJSON geometry."""
    if geometry["type"] == "Polygon":
        return [geometry["coordinates"][0]]
    return [polygon[0] for polygon in geometry["coordinates"]]


def _label_point(geometry: dict) -> tuple[float, float]:
    """Center of the largest polygon (area-weighted centroid), as (lon, lat)."""

    def centroid(ring):
        area = cx = cy = 0.0
        for (x0, y0), (x1, y1) in itertools.pairwise(ring):
            cross = x0 * y1 - x1 * y0
            area += cross
            cx += (x0 + x1) * cross
            cy += (y0 + y1) * cross
        return abs(area), cx / (3 * area), cy / (3 * area)

    _, lon, lat = max(centroid(ring) for ring in _rings(geometry))
    return lon, lat


def district_map(
    districts: pd.DataFrame, boundaries: dict, measure: Measure, selected: int | None
) -> go.Figure:
    fig = go.Figure(
        go.Choroplethmap(
            geojson=boundaries,
            featureidkey="properties.district",
            locations=districts.index,
            z=districts[measure.rate],
            colorscale=[[i / (len(BLUES) - 1), c] for i, c in enumerate(BLUES)],
            marker={"opacity": 0.85, "line": {"color": "white", "width": 1.5}},
            customdata=_customdata(districts, measure),
            hovertemplate=_hover(measure),
            colorbar={
                "tickformat": _percent_format(districts[measure.rate]),
                "thickness": 12,
                "len": 0.7,
                "outlinewidth": 0,
                "title": {"text": measure.short, "side": "right", "font": FONT},
                "tickfont": FONT,
            },
        )
    )
    features = {f["properties"]["district"]: f for f in boundaries["features"]}

    if selected is not None:
        lons, lats = [], []
        for ring in _rings(features[selected]["geometry"]):
            lons += [x for x, _ in ring] + [None]
            lats += [y for _, y in ring] + [None]
        fig.add_trace(
            go.Scattermap(
                lon=lons,
                lat=lats,
                mode="lines",
                line={"color": INK, "width": 3},
                hoverinfo="skip",
            )
        )

    # A white badge with the district number in the middle of each district.
    points = [_label_point(features[d]["geometry"]) for d in districts.index]
    fig.add_trace(
        go.Scattermap(
            lon=[lon for lon, _ in points],
            lat=[lat for _, lat in points],
            mode="markers+text",
            text=[str(d) for d in districts.index],
            marker={"size": 24, "color": "white"},
            textfont={"size": 13, "color": INK, "weight": "bold"},
            hoverinfo="skip",
        )
    )

    all_lons = [
        x for f in boundaries["features"] for r in _rings(f["geometry"]) for x, _ in r
    ]
    all_lats = [
        y for f in boundaries["features"] for r in _rings(f["geometry"]) for _, y in r
    ]
    center = {
        "lon": (min(all_lons) + max(all_lons)) / 2,
        "lat": (min(all_lats) + max(all_lats)) / 2,
    }
    zoom = 10.75
    fig.update_layout(
        map={"style": "carto-positron", "center": center, "zoom": zoom},
        # A button on the map that puts it back where it started.
        updatemenus=[
            {
                "type": "buttons",
                "showactive": False,
                "buttons": [
                    {
                        "label": "⟲ Recenter map",
                        "method": "relayout",
                        "args": [{"map.center": center, "map.zoom": zoom}],
                    }
                ],
                "x": 0.01,
                "y": 0.99,
                "xanchor": "left",
                "yanchor": "top",
                "pad": {"l": 4, "t": 4},
                "bgcolor": "white",
                "bordercolor": MUTED,
                "font": {**FONT, "size": 13},
            }
        ],
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        height=480,
        showlegend=False,
        font=FONT,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def district_bars(
    districts: pd.DataFrame, city_rate: float, measure: Measure, selected: int | None
) -> go.Figure:
    """Each district's share side by side, with the selected one highlighted."""
    colors = [
        ACCENT if selected is None or d == selected else MUTED for d in districts.index
    ]
    rates = districts[measure.rate]
    fig = go.Figure(
        go.Bar(
            y=[f"District {d}" for d in districts.index],
            x=rates,
            orientation="h",
            marker={"color": colors, "line": {"width": 0}},
            text=[f"{r:.1%}" for r in rates],
            textposition="outside",
            textfont={"color": INK, "size": 13},
            cliponaxis=False,
            customdata=_customdata(districts, measure),
            hovertemplate=_hover(measure),
        )
    )
    fig.add_vline(
        x=city_rate,
        line={"color": INK_2, "width": 1.5, "dash": "dash"},
        annotation={
            "text": f"Mableton overall: {city_rate:.1%}",
            "font": {"color": INK_2, "size": 12},
            "yanchor": "bottom",
        },
        annotation_position="top",
    )
    fig.update_layout(
        height=480,
        margin={"l": 8, "r": 16, "t": 36, "b": 40},
        bargap=0.45,
        barcornerradius=4,
        font=FONT,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis={
            "tickformat": ".0%",
            "range": [0, rates.max() * 1.25],
            "gridcolor": GRID,
            "zeroline": True,
            "zerolinecolor": MUTED,
            "tickfont": {"color": INK_2},
        },
        yaxis={
            "autorange": "reversed",
            "automargin": True,
            "ticksuffix": "  ",
            "tickfont": {"size": 14},
        },
        hoverlabel={"bgcolor": "white", "font": FONT},
    )
    return fig
