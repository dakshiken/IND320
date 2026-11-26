"""Cached data loaders for the Streamlit pages (waiting time: spinners, progress bars and st.cache_data)."""
import json

import pandas as pd
import streamlit as st

from modules import state
from modules.currency import download_rates
from modules.weather import download_weather

N_POINTS = 50        # random locations per area (anomaly page)
N_LONG = 10          # fewer locations for multi-year downloads
WEATHER = {"temperature_2m": "Temperature (°C)", "precipitation": "Precipitation (mm/h)", "rain": "Rain (mm/h)",
           "snowfall": "Snowfall (cm/h)", "wind_speed_10m": "Wind speed 10 m (km/h)", "wind_gusts_10m": "Wind gusts 10 m (km/h)"}


@st.cache_data
def geojson(area_type):
    """The areas of one type (EL, VASS or NO) from data/areas.geojson."""
    gj = json.load(open("data/areas.geojson"))
    return {"type": "FeatureCollection", "features": [f for f in gj["features"] if f["properties"]["type"] == area_type]}


@st.cache_data
def months():
    """All months that Magasinstatistikk has data for (options of the time sliders)."""
    from modules.data_loader import download_all
    return sorted(download_all()["Date"].dt.to_period("M").astype(str).unique())


@st.cache_data(ttl=86400, show_spinner=False)
def weather_year(area, year, variable, n_points):
    """Hourly weather for one area, year and property. Every year is cached, so longer periods are built from cached years."""
    last = pd.Timestamp.today().normalize() - pd.Timedelta(days=7)       # ERA5 lags a few days
    end = min(pd.Timestamp(f"{year}-12-31"), last)
    if pd.Timestamp(f"{year}-01-01") > end:
        return pd.DataFrame(columns=[variable])
    return download_weather(area, f"{year}-01-01", end.strftime("%Y-%m-%d"), n_points, (variable,))


def weather_range(area, first_year, last_year, variables, n_points=N_LONG):
    """Hourly weather for several years and properties, with a progress bar."""
    jobs = [(v, y) for v in variables for y in range(first_year, last_year + 1)]
    bar = st.progress(0.0, text="Downloading weather ...")
    parts = {}
    for i, (variable, year) in enumerate(jobs):
        bar.progress(i / len(jobs), text=f"Downloading {WEATHER.get(variable, variable)}, {area}, {year} ...")
        parts.setdefault(variable, []).append(weather_year(area, year, variable, n_points))
    bar.empty()
    return pd.concat([pd.concat(frames) for frames in parts.values()], axis=1)


@st.cache_data(ttl=3600, show_spinner="Downloading exchange rates from Norges Bank ...")
def rates(start, end):
    return download_rates(start, end)


def period_slider(where=st, label="Time frame (months)"):
    """Range slider over the months of Magasinstatistikk. The time frame is shared by all pages (see state.py)."""
    return state.period_slider(months(), where, label)


def show_error(error, source, hint):
    """Show a useful message instead of a traceback (the page goes on)."""
    st.error(f"Could not get data from **{source}**: {error}")
    st.caption(hint)


def stop_on_error(error, source, hint):
    """Show a useful message instead of a traceback and stop the page."""
    show_error(error, source, hint)
    st.stop()
