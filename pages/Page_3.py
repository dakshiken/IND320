import streamlit as st

from modules.data_loader import AREA_TYPES, VALUE_COLS, download_all, load_data

#page configuration
st.set_page_config(page_title="Reservoir Plot", page_icon="📈", layout="wide")
st.title("📈  Reservoir Plot  📈")

#months that the API provides, used as the options of the slider
months = sorted(download_all()["Date"].dt.to_period("M").astype(str).unique())

#area type (radio), column (selectbox) and download interval (select_slider)
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    area_type = st.radio("Area type", AREA_TYPES)
with col2:
    column_choice = st.selectbox("Column to plot", ["All columns"] + VALUE_COLS)
with col3:
    #slider decides which months are loaded
    start, end = st.select_slider(
        "Download interval (months)", options=months,
        value=(months[max(0, len(months) - 36)], months[-1]),
    )

#only the chosen area type and months are loaded
df = load_data(area_type, start, end)
if df.empty:
    st.warning("No data for this selection.")
    st.stop()

if column_choice != "All columns":
    #one line for each area number
    st.subheader(f"{column_choice}, {start} to {end}")
    wide = df.pivot_table(index="Date", columns="Area", values=column_choice)
    st.line_chart(wide, x_label="Date", y_label=column_choice)
else:
    #one chart per area number with all columns min-max scaled to 0-1.
    #constant column (range 0) gets range 1, so the line stays at 0 instead of disappearing.
    for area, g in df.groupby("Area", sort=False):
        g = g.set_index("Date")[VALUE_COLS]
        rng = (g.max() - g.min()).replace(0, 1)
        st.subheader(f"{area}: all columns (normalised), {start} to {end}")
        st.line_chart((g - g.min()) / rng, x_label="Date", y_label="Normalised value (0-1)")

st.caption(f"Showing {df['Date'].nunique()} weekly observations for {df['Area'].nunique()} area(s) between {start} and {end}.")