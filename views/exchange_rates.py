import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules import app_data, guide, state
from modules.theme import style

st.title(":material/currency_exchange: Exchange rates")
guide.intro(
    "What does one euro or one US dollar cost in Norwegian kroner? The rates come from Norges Bank, one rate for every business day.",
    [
        "The **period** starts with the time frame from the Home page. You can change the dates here; this does not change the choice on Home.",
        "Choose **EUR/NOK**, **USD/NOK** or both. EUR/NOK = how many kroner you pay for one euro.",
        "The numbers above the plot show the latest rate and how much it has changed since the first day. A higher rate means a weaker krone.",
        "There are no rates on weekends and holidays, so those days are empty.",
    ],
    uses=("time frame",),
)

today = datetime.date.today()
frame = state.period()                       # months from Home, or the last 12 months if none chosen yet
if frame:
    first, last = pd.Period(frame[0]).start_time.date(), min(pd.Period(frame[1]).end_time.date(), today)
else:
    first, last = today - datetime.timedelta(days=365), today
if first >= last:
    first = last - datetime.timedelta(days=30)
# the key holds the time frame: a new choice on Home resets the dates, a change here stays until then
period = st.date_input("Period", value=(first, last), max_value=today, key=f"fx_period_{first}_{last}",
                       help="First and last day. It starts with the time frame from the Home page.")
currencies = st.multiselect("Currencies", ["EUR/NOK", "USD/NOK"], default=["EUR/NOK", "USD/NOK"])
if len(period) != 2:
    st.info("Choose a start and an end date.")
    st.stop()
if not currencies:
    st.info("Choose at least one currency.")
    st.stop()

try:
    rates = app_data.rates(period[0].isoformat(), period[1].isoformat())
except Exception as e:
    app_data.stop_on_error(e, "Norges Bank", "The rates are only published on business days; try another period or try again later.")
rates = rates[currencies].dropna(how="all")
if rates.empty:
    st.warning("No rates in this period (weekends and holidays have none).")
    st.stop()

# latest rate and change over the period
cols = st.columns(len(currencies))
for col, c in zip(cols, currencies):
    series = rates[c].dropna()
    col.metric(c, f"{series.iloc[-1]:.4f}", f"{series.iloc[-1] - series.iloc[0]:+.4f} since {series.index[0]:%Y-%m-%d}")
fig = go.Figure([go.Scatter(x=rates.index, y=rates[c], name=c, mode="lines") for c in currencies])
fig.update_yaxes(title_text="NOK")
st.plotly_chart(style(fig, "Norges Bank exchange rates", height=450), theme=None)
if rates.isna().any().any():
    st.caption("Days without a rate for one of the currencies are left empty.")
