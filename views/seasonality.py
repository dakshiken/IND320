import streamlit as st

from modules import app_data, guide, state
from modules.analysis import spectrogram_plot, stl_plot
from modules.data_loader import load_data

st.title(":material/waves: Seasonality")
guide.intro(
    "Does the fill degree repeat a pattern every year? Two methods show it: STL decomposition and a spectrogram of the weekly fill degree.",
    [
        "Choose an **area**. It is the same as on the Home page, and a change here is used on the other pages too.",
        "**STL decomposition** splits the curve in three parts: the **trend** (slow change over many years), the **seasonal** part "
        "(the pattern that repeats every year) and the **residual** (what is left). *Robust* makes the result less sensitive to strange weeks.",
        "**Spectrogram**: the x-axis is time and the y-axis is how often a pattern repeats (cycles per year). "
        "A bright band at 1 cycle per year means a strong yearly pattern. You can see if it changes over the years.",
        "This page uses the whole history (STL needs at least three years), so it does not use the time frame from Home.",
    ],
    uses=("area",),
)

# area is shared with the other pages
area_type, area = state.area_picker()
try:
    df = load_data(area_type)
except Exception as e:
    app_data.stop_on_error(e, "NVE Magasinstatistikk", "Check your connection and reload the page.")
fill = df[df["Area"] == area].set_index("Date")["Fill Degree"].sort_index()
if fill.notna().sum() < 3 * 52:
    st.warning("Less than three years of data for this area: STL and the spectrogram need a longer series.")
    st.stop()
if fill.isna().any():
    st.caption(f"{int(fill.isna().sum())} missing weeks are filled by interpolation.")

# tabs: STL and spectrogram
tab_stl, tab_spec = st.tabs(["STL decomposition", "Spectrogram"])

with tab_stl:
    c1, c2, c3 = st.columns(3)
    seasonal = c1.slider("Seasonal smoother", 3, 51, 13, step=2,             # odd numbers
                         help="A higher number lets the yearly pattern change more slowly from year to year. Odd numbers only.")
    trend = c2.slider("Trend smoother", 53, 301, 105, step=2,                # odd, larger than 52 weeks
                      help="A higher number gives a smoother, stiffer trend line. Odd numbers only.")
    robust = c3.checkbox("Robust", value=True, help="Strange weeks get less weight, so they do not disturb the trend and the yearly pattern.")
    st.plotly_chart(stl_plot(fill, seasonal, trend, robust), theme=None)

with tab_spec:
    c1, c2 = st.columns(2)
    window = c1.slider("Window length (weeks)", 26, 520, 156, step=26,
                       help="The curve is cut in windows of this length. Long windows show slow patterns clearly but give a blurrier timeline.")
    # overlap must be smaller than the window
    overlap = c2.slider("Window overlap (weeks)", 0, window - 1, window // 2,
                        help="How many weeks neighbouring windows share. More overlap gives a smoother picture.")
    st.plotly_chart(spectrogram_plot(fill, window, overlap), theme=None)
