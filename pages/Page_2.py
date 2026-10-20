import pandas as pd
import streamlit as st

from modules.data_loader import AREA_TYPES, VALUE_COLS, load_data

# Page configuration
st.set_page_config(page_title="Reservoir Table", page_icon="📊", layout="wide")
st.title("📊  Reservoir Table  📊")
st.markdown(
    "Data is downloaded live from the NVE Magasinstatistikk API. One row per area number. "
    "Each sparkline shows the trend for the selected months."
)

# EL (bidding zones), NO (whole country) or VASS (watercourse areas)
area_type = st.radio("Area type", AREA_TYPES, horizontal=True)
df = load_data(area_type=area_type)

# Sikre at Date er datetime og lag måned-slider
if not df.empty and "Date" in df.columns:
    df["Date"] = pd.to_datetime(df["Date"])
    
    # Konverter datoer til måneder for slideren
    month = df["Date"].dt.to_period("M")
    months = [str(period) for period in month.unique()]
    
    # Velg standardverdi (siste 5 år hvis tilgjengelig, ellers hele perioden)
    default_start = months[-60] if len(months) >= 60 else months[0]
    default_end = months[-1]
    
    start, end = st.select_slider("Months to show", options=months, value=(default_start, default_end))
    
    # Filtrer subset basert på valgt start- og sluttmåned
    after_start = month >= pd.Period(start)
    before_end = month <= pd.Period(end)
    subset = df[after_start & before_end]
else:
    subset = df

# One row per area number, one sparkline column per data column
rows = []
for area, g in subset.groupby("Area", sort=False):
    if g.empty:
        continue
    row = {"Area": area}
    row.update({col: g[col].tolist() for col in VALUE_COLS})
    rows.append(row)

summary_df = pd.DataFrame(rows)

if not summary_df.empty:
    st.write(f"Showing weekly values from {start} to {end}.")
    st.dataframe(
        summary_df,
        column_config={col: st.column_config.LineChartColumn(col) for col in VALUE_COLS},
        hide_index=True,
    )
else:
    st.warning("Ingen data tilgjengelig for den valgte perioden.")

# Raw downloaded data in an expander
with st.expander("Show raw imported data"):
    st.dataframe(df)