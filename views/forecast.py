import datetime
import json

import pandas as pd
import streamlit as st

from modules import app_data, guide, state
from modules.app_data import WEATHER
from modules.data_loader import load_data
from modules.forecast import forecast_fill, forecast_plot, weekly_extra
from modules.mongo import get_net_flow

st.title(":material/auto_graph: Forecast")
guide.intro(
    "What will the fill degree be in the coming weeks? A model (River SNARIMAX) learns from the past weeks and calculates a forecast.",
    [
        "Choose **what to forecast**: a *back-test* (the model forecasts a period that has already happened, so you can compare) or *the coming weeks*.",
        "The **purple line** is the forecast. The **shaded band** is the interval: the real value should be inside it in about 8 of 10 cases. "
        "The **green dotted line** is what really happened (only for a back-test).",
        "Press **▶ Play** under the plot to see the forecast grow week by week.",
        "**Extra data** (weather, exchange rates, net export) can be given to the model as hints. More data is not always better.",
        "**Model settings** are for advanced users. The defaults are the best settings from the back-test in the notebook.",
        "**Mean absolute error** is the average size of the mistake on the 0-1 scale of the fill degree. Lower is better.",
    ],
    uses=("area", "time frame"),
)

# defaults come from the notebook (best back-test setting); fallback if the file is missing
D = dict(p=2, d=0, q=1, m=52, sp=1, sd=0, sq=0, history=260, epochs=10, lr=0.05, exog=[], future="seasonal")
try:
    D.update(json.load(open("data/forecast_defaults.json")))
except FileNotFoundError:
    pass

# area and time frame are shared with Home
area_type, area = state.area_picker()
try:
    df = load_data(area_type)
except Exception as e:
    app_data.stop_on_error(e, "NVE Magasinstatistikk", "Check your connection and reload the page.")
fill = df[df["Area"] == area].set_index("Date")["Fill Degree"].sort_index()

mode = st.radio("What to forecast", ["Back-test: the time frame from Home", "Forecast the coming weeks"], horizontal=True, key="fc_mode",
                help="Back-test: the model learns from the weeks before the time frame and forecasts the time frame, so the forecast can be compared with what really happened. "
                     "Coming weeks: the model learns from all data and looks into the future.")
if mode.startswith("Back"):
    start, end = (pd.Period(m) for m in app_data.period_slider(label="Time frame to forecast (the same as on Home)"))
    before = fill.index[fill.index < start.start_time]
    inside = fill[start.start_time:end.end_time]
    if len(before) == 0 or inside.empty:
        st.warning("No data in this time frame: choose another one.")
        st.stop()
    origin, horizon = before[-1], min(len(inside), 52)
    st.caption(f"The model is trained on the weeks before {start} and forecasts {horizon} weeks (the real values are shown for comparison).")
else:
    origin = fill.index[-1]
    horizon = st.slider("Weeks ahead", 1, 52, 26, key="fc_horizon", help="How many weeks into the future the model looks.")

# model settings
with st.expander("Model settings", expanded=False):
    c = st.columns(4)
    p = c[0].number_input("p (AR)", 0, 10, int(D["p"]), key="fc_p", help="How many of the latest weeks the model looks at.")
    d = c[1].number_input("d (differencing)", 0, 2, int(D["d"]), key="fc_d", help="0 = use the values as they are, 1 = use the change from week to week.")
    q = c[2].number_input("q (MA)", 0, 10, int(D["q"]), key="fc_q", help="How many of its latest mistakes the model uses to correct itself.")
    history = c[3].slider("History (weeks)", 52, 780, int(D["history"]), step=26, key="fc_history", help="How many weeks of the past the model learns from.")
    c = st.columns(4)
    m = c[0].number_input("m (season length, weeks)", 1, 104, int(D["m"]), key="fc_m", help="The length of the yearly pattern in weeks (52).")
    sp = c[1].number_input("sp (seasonal AR)", 0, 3, int(D["sp"]), key="fc_sp", help="The same as p, but for the same week in earlier years.")
    sd = c[2].number_input("sd (seasonal differencing)", 0, 2, int(D["sd"]), key="fc_sd", help="The same as d, but compared with the same week one year earlier.")
    sq = c[3].number_input("sq (seasonal MA)", 0, 3, int(D["sq"]), key="fc_sq", help="The same as q, but for the same week in earlier years.")
    c = st.columns(3)
    lr = c[0].select_slider("Learning rate", [0.001, 0.005, 0.01, 0.02, 0.05, 0.1], value=D["lr"] if D["lr"] in [0.001, 0.005, 0.01, 0.02, 0.05, 0.1] else 0.05, key="fc_lr",
                         help="The size of every learning step. Too high gives an unstable model, too low learns slowly.")
    epochs = c[1].slider("Passes over the history", 1, 40, int(D["epochs"]), key="fc_epochs", help="How many times the model goes through the history while it learns.")
    interval = c[2].checkbox("80 % interval (quantile models)", value=True, key="fc_interval", help="Shows a band where the real value should be in about 8 of 10 cases.")

# extra data (exogenous variables)
weather_options = list(WEATHER) if area_type != "NO" else []
options = weather_options + ["EUR/NOK", "USD/NOK", "net_export_MW"]
labels = {**WEATHER, "EUR/NOK": "EUR/NOK (Norges Bank)", "USD/NOK": "USD/NOK (Norges Bank)", "net_export_MW": "Net export (ENTSO-E, from 2024)"}
exog = st.multiselect("Extra data for the model (exogenous variables)", options, default=[v for v in D["exog"] if v in options], format_func=labels.get, key="fc_exog",
                      help="Hints for the model. Choose none to forecast from the fill degree alone. Weather comes from Open-Meteo, exchange rates from Norges Bank and net export from ENTSO-E.")
if area_type == "NO":
    st.caption("Weather is downloaded per EL or VASS area, so it is not available for Norway as a whole.")
future = st.radio("Values of the extra data in the forecast weeks", ["seasonal", "actual"], horizontal=True, key="fc_future",
                  help="The model needs the extra data also for the weeks it forecasts. In real life they are not known yet, so the typical values of that time of the year are used. "
                       "'Real values' is only possible in a back-test and gives a better but too optimistic result.",
                  index=0 if D["future"] == "seasonal" else 1,
                  format_func={"seasonal": "Seasonal mean of the history (a real forecast)", "actual": "Real values (a back-test, optimistic)"}.get)

# load the chosen sources (cached, each with its own progress)
extra = None
if exog:
    weather_vars = [v for v in exog if v in WEATHER]
    first_year = max(fill.index[0].year, (origin - pd.Timedelta(weeks=history)).year - 1)
    last_year = min((origin + pd.Timedelta(weeks=horizon)).year, datetime.date.today().year)
    parts = {}
    if weather_vars:
        try:
            parts["weather"] = app_data.weather_range(area, first_year, last_year, weather_vars)
        except Exception as e:
            app_data.stop_on_error(e, "Open-Meteo", "The free API allows 600 calls per minute and 5,000 per hour. Wait a little, or use fewer weather properties.")
    currencies = [v for v in exog if v.endswith("/NOK")]
    if currencies:
        try:
            parts["rates"] = app_data.rates(f"{first_year}-01-01", datetime.date.today().isoformat())[currencies]
        except Exception as e:
            app_data.stop_on_error(e, "Norges Bank", "Try again later, or remove the exchange rates.")
    if "net_export_MW" in exog:
        try:
            parts["flows"] = get_net_flow()
        except Exception as e:
            app_data.stop_on_error(e, "MongoDB", "Check the MONGO_URI secret, or remove the net export.")
    extra = weekly_extra(**parts)

# train and forecast (cached per input)
run = st.cache_data(show_spinner="Training the model ...")(forecast_fill)
try:
    result, info = run(fill, extra, exog=exog, origin=origin, horizon=horizon, history=history, p=p, d=d, q=q, m=m, sp=sp, sd=sd, sq=sq,
                       lr=lr, epochs=epochs, future=future, interval=interval)
except ValueError as e:
    st.warning(f"The model could not be trained: {e}. Use a longer history or fewer exogenous variables (net export exists from 2024 only).")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Mean absolute error", "-" if pd.isna(info["mae"]) else f"{info['mae']:.4f}",
          help="The average size of the mistake on the scale of the fill degree (0 to 1). Lower is better. It can only be calculated when the real values are known.")
c2.metric("Training weeks", info["n_train"], f"{info['train_start']:%Y-%m-%d} to {info['train_end']:%Y-%m-%d}", delta_color="off",
          help="The number of weeks the model learned from.")
c3.metric("Time", f"{info['seconds']:.1f} s", help="How long it took to train the model and make the forecast.")
if not pd.isna(info["mae"]):
    points = round(info["mae"] * 100)
    st.info(f"**In plain words**  \nOn average the forecast is {points} percentage point{'' if points == 1 else 's'} away from the real fill degree (1 = full reservoirs).")
st.plotly_chart(forecast_plot(fill, result), theme=None)
st.caption("Press ▶ Play under the plot, or drag the slider, to see the forecast week by week.")
with st.expander("Forecast table"):
    st.dataframe(result)
    st.download_button("Download as CSV", result.to_csv().encode(), file_name=f"forecast_{area.replace(' ', '')}.csv")
