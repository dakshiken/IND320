import pandas as pd
import plotly.express as px
import streamlit as st

from modules import app_data, guide, state
from modules.data_loader import VALUE_COLS, load_data
from modules.theme import style

st.title(":material/water_medium: Reservoirs")
guide.intro(
    "How full are the water reservoirs, week by week? You see every area of the chosen type.",
    [
        "Choose the **area type** and the **time frame**. They are the same as on the Home page, and a change here is used on the other pages too.",
        "**Table** tab: every row is an area. The small line in a column shows how that value changed from week to week.",
        "**Plot** tab: choose one column to see it as lines, or *All columns* to compare their shapes (every column is then scaled to 0-1).",
        "**Fill Degree** is how full the reservoirs are: 0 = empty, 1 = full. **Capacity** is how much energy they can hold and "
        "**Fill Volume** is how much is stored now (both in TWh).",
        "The data comes from NVE Magasinstatistikk and has one value per week.",
    ],
    uses=("area type", "time frame"),
)

area_type = state.type_picker()
try:
    df = load_data(area_type)
except Exception as e:
    app_data.stop_on_error(e, "NVE Magasinstatistikk", "Check your connection and reload the page.")
if df.empty:
    st.warning("No data for this area type.")
    st.stop()

# one time frame for table and plot (shared with Home)
start, end = app_data.period_slider()
month = df["Date"].dt.to_period("M").astype(str)
subset = df[(month >= start) & (month <= end)]
if subset.empty:
    st.warning("No data in this time frame: choose another one.")
    st.stop()

# sparkline table and plot on one page
tab_table, tab_plot = st.tabs(["Table", "Plot"])

with tab_table:
    # one row per area, one sparkline per column
    rows = [{"Area": area, **{col: g[col].tolist() for col in VALUE_COLS}} for area, g in subset.groupby("Area", sort=False)]
    st.write(f"Weekly values from {start} to {end}. The small line in each cell shows the change from week to week.")
    st.dataframe(pd.DataFrame(rows), column_config={col: st.column_config.LineChartColumn(col) for col in VALUE_COLS}, hide_index=True)
    with st.expander("Show raw imported data"):
        st.dataframe(df)

with tab_plot:
    column = st.selectbox("Column to plot", ["All columns"] + VALUE_COLS, key="plot_column",
                          help="Choose one column to see its real values, or all columns scaled to 0-1 to compare their shapes.")
    if column != "All columns":
        st.plotly_chart(style(px.line(subset, x="Date", y=column, color="Area"), f"{column}, {start} to {end}"), theme=None)
    else:
        # scale every column to 0-1 (a constant column stays at 0), one panel per area
        long = subset.melt(id_vars=["Date", "Area"], value_vars=VALUE_COLS, var_name="Column", value_name="value")
        g = long.groupby(["Area", "Column"])["value"]
        long["Normalised value (0-1)"] = (long["value"] - g.transform("min")) / (g.transform("max") - g.transform("min")).replace(0, 1)
        fig = px.line(long, x="Date", y="Normalised value (0-1)", color="Column", facet_row="Area")
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        st.plotly_chart(style(fig, f"All columns (normalised), {start} to {end}", height=260 * long["Area"].nunique() + 80), theme=None)
    st.caption(f"{subset['Date'].nunique()} weekly observations for {subset['Area'].nunique()} area(s).")
