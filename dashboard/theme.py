"""Color schemes and light/dark mode, for the page (Streamlit's theme) and the charts."""

from dataclasses import dataclass

import streamlit as st
from streamlit import config


def _ramp(low: str, mid: str, high: str, steps: int = 6) -> list[str]:
    """Evenly spaced colors from low through mid to high (for "less" to "more")."""

    def rgb(hex_color):
        return [int(hex_color[i : i + 2], 16) for i in (1, 3, 5)]

    def mix(a, b, t):
        return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))

    a, b, c = rgb(low), rgb(mid), rgb(high)
    colors = []
    for i in range(steps):
        t = 2 * i / (steps - 1)
        colors.append(mix(a, b, t) if t <= 1 else mix(b, c, t - 1))
    return colors


@dataclass(frozen=True)
class Scheme:
    divider: str  # Streamlit's name for the closest heading-underline color
    light_accent: str
    light_ramp: tuple[str, str, str]  # low, middle, high on a light map
    dark_accent: str
    dark_ramp: tuple[str, str, str]  # low, middle, high on a dark map


SCHEMES = {
    # The city's brand green, #297e47, with lighter and darker steps of the same hue.
    "Mableton green": Scheme(
        divider="green",
        light_accent="#297e47",
        light_ramp=("#ddefe3", "#297e47", "#0f3a20"),
        dark_accent="#3fa866",  # the brand green lifted so it reads on a dark page
        dark_ramp=("#1b4229", "#297e47", "#a3d9b5"),
    ),
    "Blue": Scheme(
        divider="blue",
        light_accent="#2a78d6",
        light_ramp=("#cde2fb", "#3987e5", "#104281"),
        dark_accent="#3987e5",
        dark_ramp=("#163a66", "#3987e5", "#b7d3f6"),
    ),
    "Purple": Scheme(
        divider="violet",
        light_accent="#6250d6",
        light_ramp=("#e6e2fb", "#7a6ae0", "#2e2380"),
        dark_accent="#9085e9",
        dark_ramp=("#2f2766", "#7a6ae0", "#d3cdf8"),
    ),
}


@dataclass(frozen=True)
class Palette:
    dark: bool
    divider: str
    accent: str  # the selected district, buttons
    ramp: list[str]  # map colors, less to more
    page: str
    raised: str  # widget and card backgrounds
    surface: str  # tooltips and the map's button
    ink: str
    ink_2: str
    muted: str  # unselected bars, borders
    grid: str
    basemap: str


def palette(dark: bool, scheme_name: str) -> Palette:
    scheme = SCHEMES[scheme_name]
    if dark:
        return Palette(
            dark=True,
            divider=scheme.divider,
            accent=scheme.dark_accent,
            ramp=_ramp(*scheme.dark_ramp),
            page="#121211",
            raised="#1f1f1d",
            surface="#262624",
            ink="#f0efec",
            ink_2="#c3c2b7",
            muted="#4a4944",
            grid="#2c2c2a",
            basemap="carto-darkmatter",
        )
    return Palette(
        dark=False,
        divider=scheme.divider,
        accent=scheme.light_accent,
        ramp=_ramp(*scheme.light_ramp),
        page="#f9f9f7",
        raised="#f0efec",
        surface="#ffffff",
        ink="#0b0b0b",
        ink_2="#52514e",
        muted="#c3c2b7",
        grid="#e1e0d9",
        basemap="carto-positron",
    )


def apply(p: Palette) -> None:
    """Points Streamlit's theme at this palette.

    Streamlit only has one theme setting per server, which it sends to the browser at the
    start of each run. So if it isn't this visitor's choice yet, set it and run again.
    (On Firebase each visitor has their own in-browser server; on a shared server a visitor
    may get one extra rerun after someone else changes it.)
    """
    wanted = {
        "theme.base": "dark" if p.dark else "light",
        "theme.primaryColor": p.accent,
        "theme.backgroundColor": p.page,
        "theme.secondaryBackgroundColor": p.raised,
        "theme.textColor": p.ink,
        # Heading underlines use a named color; make that name the scheme's accent.
        f"theme.{p.divider}Color": p.accent,
    }
    if any(config.get_option(key) != value for key, value in wanted.items()):
        for key, value in wanted.items():
            config.set_option(key, value)
        st.rerun()
