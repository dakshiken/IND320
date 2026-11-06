import streamlit as st

from modules.analysis import spectrogram_plot, stl_plot
from modules.data_loader import AREA_TYPES, load_data

#page configuration
st.set_page_config(page_title="STL and Spectrogram", page_icon="🌊", layout="wide")
st.title("🌊  STL and Spectrogram 🌊 ")
st.markdown("Analysis of the weekly degree of filling from the NVE Magasinstatistikk API.")

# area selector
area_type = st.radio("Area type", AREA_TYPES, horizontal=True)
df = load_data(area_type)
area = st.selectbox("Area", df["Area"].unique())
fill = df[df["Area"] == area].set_index("Date")["Fill Degree"]

tab_stl, tab_spec = st.tabs(["STL decomposition", "Spectrogram"])

with tab_stl:
    c1, c2, c3 = st.columns(3)
    seasonal = c1.slider("Seasonal smoother", 3, 51, 13, step=2)     
    trend = c2.slider("Trend smoother", 53, 301, 105, step=2)   
    robust = c3.checkbox("Robust", value=True)
    st.pyplot(stl_plot(fill, seasonal, trend, robust))

with tab_spec:
    c1, c2 = st.columns(2)
    window = c1.slider("Window length (weeks)", 26, 520, 156, step=26)
    overlap = c2.slider("Window overlap (weeks)", 0, window - 1, window // 2)
    st.pyplot(spectrogram_plot(fill, window, overlap))