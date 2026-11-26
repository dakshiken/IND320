"""Help texts for new users: page intro, plain-word results, glossary and previous/next links."""
import pandas as pd
import streamlit as st

from modules import state

GLOSSARY = [
    ("Reservoir", "A large lake behind a dam. The water is stored there and used to make electricity."),
    ("Fill degree", "How full the reservoirs are, from 0 (empty) to 1 (full). 0.75 means 75 % full."),
    ("Price area (EL 1 to 5)", "Norway is divided into five areas (NO1 to NO5). Each has its own electricity price."),
    ("Water area (VASS 1 to 3)", "Three watercourse areas (river basins) that NVE uses for the reservoir statistics."),
    ("TWh, GWh, MW", "Units for energy and power. 1 TWh = 1,000 GWh. A reservoir holds energy in TWh. MW tells how much power flows at one moment."),
    ("Time frame", "The first and the last month that you look at."),
    ("Weather property", "One kind of weather data, for example temperature, rain or wind speed. It is the average over random places in the area."),
    ("Trend and season (STL)", "A way to split a curve in a slow long-term change (trend), a pattern that repeats every year (season) and what is left over (residual)."),
    ("Outlier and anomaly", "A value that is very different from what is normal. SPC and LOF are two different methods to find them."),
    ("Correlation", "A number from -1 to 1 that tells if two curves move together. 1 = they rise and fall together, 0 = no link, -1 = when one rises the other falls. It does not prove that one causes the other."),
    ("Lag", "A shift in time. With a lag of 4 weeks the weather of one week is compared with the reservoirs four weeks later."),
    ("Forecast", "A calculated guess about the coming weeks, made by a model that has learned from the past."),
    ("Back-test", "A forecast of a period that has already happened, so the forecast can be compared with what really happened."),
    ("Interval", "A band around the forecast. The real value should be inside the band in about 8 of 10 cases."),
    ("Mean absolute error", "The average size of the mistake of a forecast. On the fill degree scale 0.10 means that the forecast is on average 10 percentage points wrong. Lower is better."),
    ("Extra data (exogenous variables)", "Other data, such as weather or exchange rates, that the model gets as hints."),
]


def intro(what, how, uses=()):
    """Top of a page: what it shows, which choices from Home it starts with, and a 'how to use' box."""
    st.markdown(what)
    shown = []
    if "area" in uses:
        shown.append(f":material/location_on: area **{state.area()}**")
    if "area type" in uses:
        shown.append(f":material/location_on: area type **{state.TYPE_NAMES[st.session_state.sel_type]}**")
    if "time frame" in uses:
        frame = state.period()
        shown.append(f":material/calendar_month: time frame **{frame[0]} to {frame[1]}**" if frame else ":material/calendar_month: time frame **the last 12 months** (default)")
    if shown:
        text, link = st.columns([4, 1], vertical_alignment="center")
        text.caption("Starts with your choice from the Home page: " + " · ".join(shown))
        link.page_link("views/home.py", label="Change on Home", icon=":material/map:")
    with st.expander("How to use this page", icon=":material/info:"):
        st.markdown("\n".join(f"- {line}" for line in how))


def correlation_words(r):
    """A correlation in plain words."""
    if pd.isna(r):
        return "There is not enough variation in the data to say anything about a link."
    size = abs(r)
    if size < 0.1:
        return "There is almost no link between the two curves at this lag."
    word = "weak" if size < 0.3 else "moderate" if size < 0.5 else "strong" if size < 0.7 else "very strong"
    meaning = "they tend to rise and fall together." if r > 0 else "when one goes up, the other tends to go down."
    return f"There is a {word} {'positive' if r > 0 else 'negative'} link: {meaning}"


def glossary():
    with st.expander("What do the words mean?", icon=":material/help:"):
        st.markdown("\n".join(f"- **{term}**: {text}" for term, text in GLOSSARY))


def footer(order, page):
    """Previous / next links at the bottom of every page except Home."""
    i = order.index(page)
    if i == 0:
        return
    st.divider()
    left, right = st.columns(2)
    left.page_link(order[i - 1], label=f"Previous: {order[i - 1].title}", icon=":material/arrow_back:")
    if i + 1 < len(order):
        right.page_link(order[i + 1], label=f"Next: {order[i + 1].title}", icon=":material/arrow_forward:")
    else:
        right.page_link(order[0], label="Back to Home", icon=":material/home:")
