import datetime

import streamlit as st

from modules.analysis import lof_anomalies, spc_outliers
from modules.data_loader import AREA_TYPES, load_data
from modules.weather import download_weather

#page configuration
st.set_page_config(page_title="Weather Outliers", page_icon="🌦️", layout="wide")
st.title("🌦️  Weather Outliers and Anomalies 🌦️ ")
st.markdown("Hourly ERA5 weather from the Open-Meteo API for the chosen area (average over random locations).")

# local area selector
area_type = st.radio("Area type", AREA_TYPES, horizontal=True)
if area_type == "NO":
    st.info("Weather data is downloaded per region. Choose EL or VASS to continue.")
    st.stop()
area = st.selectbox("Area", load_data(area_type)["Area"].unique())
year = st.selectbox("Year", range(datetime.date.today().year - 1, 2009, -1))


@st.cache_data(ttl=86400, show_spinner="Downloading weather data from Open-Meteo ...")
def get_weather(area, year):
    # 10 random locations and two variables keep the number of api calls low
    return download_weather(area, f"{year}-01-01", f"{year}-12-31", n_points=10, variables=("temperature_2m", "precipitation"))


try:
    weather = get_weather(area, year)
except Exception as e:
    st.error(f"Could not download weather data: {e}")
    st.stop()

names = {"precipitation": "Precipitation (mm/h)", "temperature_2m": "Temperature (°C)"}
tab_spc, tab_lof = st.tabs(["Outliers (SPC)", "Anomalies (LOF)"])

with tab_spc:
    variable = st.selectbox("Variable", ["precipitation", "temperature_2m"], format_func=names.get, key="spc_variable")
    c1, c2 = st.columns(2)
    cutoff = c1.slider("DCT cut-off frequency (cycles per day)", 0.005, 0.2, 0.03, step=0.005, format="%.3f")
    n_std = c2.slider("Number of robust standard deviations", 1.0, 6.0, 3.0, step=0.5)
    fig, summary = spc_outliers(weather[variable], cutoff, n_std, names[variable])
    st.pyplot(fig)
    st.metric("Outliers", f"{summary['outliers']} of {summary['n']} hours ({summary['share']:.1%})")
    st.dataframe(summary["table"])

with tab_lof:
    variable = st.selectbox("Variable", ["temperature_2m", "precipitation"], format_func=names.get, key="lof_variable")
    contamination = st.slider("Proportion of anomalies", 0.001, 0.05, 0.01, step=0.001, format="%.3f")
    fig, summary = lof_anomalies(weather[variable], contamination, label=names[variable])
    st.pyplot(fig)
    st.metric("Anomalies", f"{summary['anomalies']} of {summary['n']} hours ({summary['share']:.1%})")
    st.dataframe(summary["table"])