import datetime

import streamlit as st

from modules import app_data, guide, state
from modules.analysis import sliding_correlation
from modules.app_data import WEATHER
from modules.data_loader import VALUE_COLS, load_data
from modules.forecast import weekly_extra

st.title(":material/scatter_plot: Correlation")
guide.intro(
    "Do the weather and the reservoirs move together? The correlation is a number between -1 and 1. "
    "A sliding window shows how the link changes over the years.",
    [
        "Choose an **area** (the same as on Home), a **weather property**, a **reservoir variable** and the **years**.",
        "**Correlation**: 1 = the two curves rise and fall together, -1 = when one rises the other falls, 0 = no link. "
        "A strong correlation does not prove that one thing causes the other.",
        "**Lag** moves the reservoir curve in time. With a lag of 4 weeks the weather of one week is compared with the reservoirs four weeks later.",
        "**Window length** is the number of weeks behind every point of the orange line (the sliding correlation).",
        "The bars at the bottom show the correlation at every lag, so you can see which lag fits best. "
        "The text below the numbers explains the result in plain words.",
    ],
    uses=("area",),
)

area_type, area = state.area_picker(types=("EL", "VASS"))
c1, c2 = st.columns(2)
weather_var = c1.selectbox("Weather property", list(WEATHER), format_func=WEATHER.get, key="corr_weather")
target = c2.selectbox("Reservoir variable (Magasinstatistikk)", VALUE_COLS, key="corr_target",      # Fill Degree is the default
                      help="Fill Degree = how full the reservoirs are (0 = empty, 1 = full).")
this_year = datetime.date.today().year
first, last = st.slider("Years", 2000, this_year - 1, (this_year - 10, this_year - 1), key="corr_years",
                        help="More years give a more reliable result, but the weather takes longer to download the first time.")
c1, c2 = st.columns(2)
lag = c1.slider("Lag (weeks)", -26, 26, 0, key="corr_lag",
                help="Positive: the weather comes first and the reservoir follows that many weeks later. Negative: the other way round.")
window = c2.slider("Window length (weeks)", 8, 156, 52, key="corr_window",
                   help="How many weeks are used for every point of the sliding correlation. A long window gives a calmer line.")

try:
    df = load_data(area_type)
except Exception as e:
    app_data.stop_on_error(e, "NVE Magasinstatistikk", "Check your connection and reload the page.")
y = df[df["Area"] == area].set_index("Date")[target].sort_index()[f"{first}-01-01":f"{last}-12-31"]
try:
    # hourly UTC to Norwegian time, then weekly mean
    x = weekly_extra(weather=app_data.weather_range(area, first, last, [weather_var]))[weather_var]
except Exception as e:
    app_data.stop_on_error(e, "Open-Meteo", "The free API allows 600 calls per minute and 5,000 per hour. Wait a little and reload.")
if y.dropna().shape[0] < window + 10:
    st.warning("Too few weeks of data for this window length.")
    st.stop()

fig, summary = sliding_correlation(x.rename(WEATHER[weather_var]), y, lag, window)
m1, m2, m3 = st.columns(3)
m1.metric(f"Correlation at lag {lag}", f"{summary['overall']:.2f}")
m2.metric("Strongest lag, weather first (weeks)", summary["best_lag"])
m3.metric("Correlation at the strongest lag", f"{summary['best_corr']:.2f}")
st.info(f"**In plain words**  \n{guide.correlation_words(summary['overall'])} (correlation {summary['overall']:.2f} at lag {lag}.)")
st.plotly_chart(fig, theme=None)
