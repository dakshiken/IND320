import datetime

import streamlit as st

from modules import app_data, guide, state
from modules.analysis import lof_anomalies, spc_outliers
from modules.app_data import N_POINTS, WEATHER

st.title(":material/thunderstorm: Weather anomalies")
guide.intro(
    f"Is the weather unusual? Hourly weather for the chosen area (Open-Meteo, ERA5, the average over {N_POINTS} random places) is checked for strange values in two ways.",
    [
        "Choose an **area** (the same as on Home) and a **year**. Then choose a **weather property** in the tab. Temperature is the default.",
        "**Outliers (SPC)**: the dashed lines are the limits of what is normal. Red dots outside the limits are outliers. "
        "*DCT cut-off* decides how closely the normal line follows the slow changes, and *robust standard deviations* decides how far from normal "
        "a value must be to count (higher = fewer outliers).",
        "**Anomalies (LOF)** finds hours that look different from the hours around them. *Proportion of anomalies* is how big a share of the hours is marked.",
        "The first time an area and a year are used, the weather is downloaded (a few seconds). After that it is kept for a day.",
    ],
    uses=("area",),
)

# shared area; weather exists for EL and VASS only
area_type, area = state.area_picker(types=("EL", "VASS"))
year = st.selectbox("Year", range(datetime.date.today().year - 1, 2009, -1), key="anomaly_year", help="One year of hourly weather is used.")


def get_series(variable):
    # one year of one property, cached for a day
    try:
        with st.spinner(f"Downloading {WEATHER[variable]} for {area}, {year} from Open-Meteo ..."):
            series = app_data.weather_year(area, year, variable, N_POINTS)[variable]
    except Exception as e:
        app_data.stop_on_error(e, "Open-Meteo", "The free API allows 600 calls per minute and 5,000 per hour. Wait a little and reload.")
    if series.isna().all():
        st.warning("Open-Meteo returned no values for this selection.")
        st.stop()
    if series.isna().any():
        st.caption(f"{int(series.isna().sum())} missing hours are filled by interpolation.")
    return series


# tabs: SPC and LOF, temperature is the default property in both
tab_spc, tab_lof = st.tabs(["Outliers (SPC)", "Anomalies (LOF)"])

with tab_spc:
    # key needed: the other tab has a selector with the same label
    variable = st.selectbox("Weather property", list(WEATHER), format_func=WEATHER.get, key="spc_property")
    c1, c2 = st.columns(2)
    cutoff = c1.slider("DCT cut-off frequency (cycles per day)", 0.005, 0.2, 0.03, step=0.005, format="%.3f",
                       help="Changes slower than this are seen as the normal season and removed before the search. A higher value lets the normal line follow the data more closely.")
    n_std = c2.slider("Number of robust standard deviations", 1.0, 6.0, 3.0, step=0.5,
                      help="How far from normal a value must be to count as an outlier. A higher number gives fewer outliers.")
    fig, summary = spc_outliers(get_series(variable), cutoff, n_std, WEATHER[variable])
    st.plotly_chart(fig, theme=None)
    st.metric("Outliers", f"{summary['outliers']} of {summary['n']} hours ({summary['share']:.1%})")
    st.dataframe(summary["table"])

with tab_lof:
    variable = st.selectbox("Weather property", list(WEATHER), format_func=WEATHER.get, key="lof_property")
    contamination = st.slider("Proportion of anomalies", 0.001, 0.05, 0.01, step=0.001, format="%.3f",
                              help="The share of the hours that is marked as anomalies. 0.010 = 1 % of the hours.")
    fig, summary = lof_anomalies(get_series(variable), contamination, label=WEATHER[variable])
    st.plotly_chart(fig, theme=None)
    st.metric("Anomalies", f"{summary['anomalies']} of {summary['n']} hours ({summary['share']:.1%})")
    st.dataframe(summary["table"])
