import random

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules import app_data, guide, state
from modules.app_data import WEATHER
from modules.data_loader import load_data
from modules.menu import GROUPS, uses_text
from modules.theme import COPPER, GROUP_COLORS, HIGHLIGHT, SEQUENTIAL, style

st.title(":material/water_medium: IND320: Water, Weather and Power")
st.markdown(
    "**How full are Norway's water reservoirs, and what affects them?** "
    "This app puts four data sources side by side, so you can look at the data, find patterns and forecast the reservoir level: "
    "reservoir levels (**NVE**), weather (**Open-Meteo**), power flows between Norway and its neighbours (**ENTSO-E**) and exchange rates (**Norges Bank**)."
)

STEPS = [
    (":material/tune: 1. Choose (optional)", "Pick an **area** and a **time frame** in the box below, or click an area on the map. This becomes the starting choice on the other pages."),
    (":material/menu_open: 2. Open a page", "Use the **menu on the left**. *Status* shows the data, *Patterns* looks for structure and *Outlook* makes a forecast."),
    (":material/sync: 3. Change it when you like", "You can skip step 1. Every page lets you choose again, and all pages use your latest choice."),
]
for col, (head, text) in zip(st.columns(3), STEPS):
    with col, st.container(border=True, height="stretch"):
        st.markdown(f"**{head}**  \n{text}")

TRANSPARENT = [[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]]
LABELS = {"fill": "Fill degree"} | WEATHER


def clicked():
    # callback of the map: a click stores the area for all pages
    points = st.session_state["area_map"].selection.points
    if points:
        state.set_area(points[0]["location"])


with st.expander("Choose an area and a time frame (optional)", expanded=True, icon=":material/map:"):
    st.markdown(
        "Whatever you choose here becomes the **starting choice on the other pages**. "
        "Or skip this and choose on each page instead."
    )
    left, right = st.columns([1, 3])
    with left:
        area_type, area = state.area_picker()
        options = {"fill": "Fill degree (how full)"} | WEATHER
        colour = st.selectbox(
            "Show on the map", list(options), format_func=options.get, key="map_colour",
            help="The areas are coloured by this value. Fill degree: 0 = empty, 1 = full. Weather: the average over the time frame "
                 "(it is downloaded the first time, which can take a little while).",
        )
        start, end = app_data.period_slider()
        st.caption("Fill degree: the value in the last week of the time frame. Weather: the average over the time frame.")
        st.button("Reset choices", icon=":material/restart_alt:", on_click=state.reset, width="stretch", help=f"Back to {state.DEFAULT_AREA} and the last 12 months.")

    with right:
        st.caption(":material/ads_click: **Click an area** to choose it. Brighter colour = higher value. Blue outline = your area.")
        try:
            if colour != "fill" and area_type == "NO":
                st.info("Weather is downloaded per price area or water area, so Norway is coloured by the fill degree.")
                colour = "fill"
            if colour == "fill":
                df = load_data(area_type)
                month = df["Date"].dt.to_period("M").astype(str)
                values = df[(month >= start) & (month <= end)].groupby("Area")["Fill Degree"].last()
            else:
                # weather: max 36 months, one download per year (cached)
                first = max(pd.Period(start), pd.Period(end) - 35)
                if first != pd.Period(start):
                    st.warning("Weather colouring is limited to 36 months: using the last 36 months of the time frame.")
                values = {}
                for a in state.AREAS[area_type]:
                    hourly = app_data.weather_range(a, first.year, pd.Period(end).year, [colour])[colour]
                    values[a] = hourly[first.start_time:pd.Period(end).end_time].mean()
                values = pd.Series(values)
        except Exception as e:
            app_data.show_error(e, "NVE Magasinstatistikk" if colour == "fill" else "Open-Meteo", "Check your connection and try again in a minute.")
            values = pd.Series(dtype=float)        # draw the map without colours

        if values.isna().all():
            st.warning("No data for this selection: choose another time frame.")

        # three layers: colours, outline of the selected area, outlines of all areas (this layer gets the clicks)
        gj = app_data.geojson(area_type)
        names = [f["properties"]["area"] for f in gj["features"]]
        z = [values.get(n) for n in names]

        def describe(v):
            if pd.isna(v):
                return "no data"
            return f"{v:.0%} full ({v:.2f})" if colour == "fill" else format(v, ".3g")

        hover = [f"<b>{n}</b><br>{LABELS[colour]}: {describe(v)}" for n, v in zip(names, z)]
        bar = "Fill degree (0 = empty, 1 = full)" if colour == "fill" else WEATHER[colour]
        common = dict(geojson=gj, featureidkey="properties.area", showscale=False)
        fig = go.Figure()
        fig.add_trace(go.Choroplethmap(locations=names, z=z, colorscale=SEQUENTIAL, marker=dict(opacity=0.75, line=dict(width=0)), hoverinfo="skip",
                                       **{**common, "showscale": True}, colorbar=dict(title=dict(text=bar, side="right"), thickness=12, len=0.6, y=0.45)))
        fig.add_trace(go.Choroplethmap(locations=[area] if area in names else [], z=[0] if area in names else [], colorscale=TRANSPARENT,
                                       marker=dict(opacity=1, line=dict(width=5, color=HIGHLIGHT)), hoverinfo="skip", **common))
        fig.add_trace(go.Choroplethmap(locations=names, z=[0] * len(names), colorscale=TRANSPARENT, text=hover, hovertemplate="%{text}<extra></extra>",
                                       marker=dict(opacity=1, line=dict(width=1, color="#8A8279")), **common))
        fig.update_layout(map=dict(style="carto-darkmatter", center=dict(lat=64.5, lon=14), zoom=3.2), margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(style(fig, height=540), theme=None, key="area_map", on_select=clicked, selection_mode="points")

# shown also when the box above is closed
st.info(f"**Your choice:** {area}, {start} to {end}. The pages below that show an area or a time frame start with it. You can change it above, or on any page.")

st.divider()
st.subheader("Pages")
st.caption("Click a name to open the page. The small labels show which of your choices the page starts with.")
for col, (group, pages) in zip(st.columns(len(GROUPS)), GROUPS.items()):
    with col:
        st.markdown(f"<h3 style='color:{GROUP_COLORS[group]};margin-bottom:0'>{group}</h3>", unsafe_allow_html=True)
        for file, title, icon, text, uses in pages:
            st.page_link(file, label=f"**{title}**", icon=icon, help=text)
            st.caption(f"{text}  \n*Starts with:* {uses_text(uses)}")

guide.glossary()
st.markdown(
    """
    - Streamlit app: https://ind320-dakshi.streamlit.app
    - GitHub: https://github.com/dakshiken/IND320
    """
)

# falling "Welcome" with CSS animation
spans = "".join(
    f'<span class="e" style="left:{random.randint(5, 95)}%; animation-delay:{random.uniform(0, 1):.1f}s">💧</span>'
    for _ in range(random.randint(3, 15))
)
st.markdown(
    f"<style>@keyframes d{{to{{top:100vh;opacity:0}}}}.e{{position:fixed;top:0;font-size:30px;color:{COPPER};animation:d 3s forwards}}</style>{spans}",
    unsafe_allow_html=True,
)
