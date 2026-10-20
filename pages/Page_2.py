import pandas as pd
import streamlit as st

from modules.data_loader import AREA_TYPES, VALUE_COLS, load_data

#page configuration
st.set_page_config(page_title="Reservoir Table", page_icon="📊", layout="wide")
st.title("📊  Reservoir Table  📊")
st.markdown(
    "data is downloaded live from the NVE Magasinstatistikk API. One row per area number. "
    "each sparkline shows the first month of that area's series."
)

#EL (bidding zones), NO (whole country) or VASS (watercourse areas)
area_type = st.radio("Area type", AREA_TYPES, horizontal=True)
df = load_data(area_type=area_type)

#one row per area number, one sparkline column per data column
rows = []
for area, g in df.groupby("Area", sort=False):
    first = g["Date"].min()
    first_month = g[(g["Date"].dt.year == first.year) & (g["Date"].dt.month == first.month)]
    row = {"Area": area, "First month": first.strftime("%Y-%m")}
    row.update({col: first_month[col].tolist() for col in VALUE_COLS})
    rows.append(row)
summary_df = pd.DataFrame(rows)

st.dataframe(
    summary_df,
    column_config={col: st.column_config.LineChartColumn(col) for col in VALUE_COLS},
    hide_index=True,
)

#raw downloaded data in an expander
with st.expander("Show raw imported data"):
    st.dataframe(df)