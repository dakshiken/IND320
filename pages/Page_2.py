import pandas as pd
import streamlit as st

from modules.data_loader import load_data

# Page configuration
st.set_page_config(page_title="Data Table", page_icon="📊", layout="wide")

# Page headers
st.title("📊 Data Table")
st.markdown(
    "One row per column of the imported CSV. **First month trend** shows a sparkline "
    "of that column's values during the first calendar month of the series."
)

# Load data
df = load_data()

# Get numeric columns (exclude Date)
value_cols = [c for c in df.columns if c != "Date"]

# Filter data for the first calendar month
first_date = df["Date"].min()
first_month_mask = (
    (df["Date"].dt.year == first_date.year) & (df["Date"].dt.month == first_date.month)
)
first_month = df.loc[first_month_mask]

# Create one row per column with lists for sparklines
table_rows = [
    {"Column": col, "First month trend": first_month[col].tolist()}
    for col in value_cols
]
summary_df = pd.DataFrame(table_rows)

# Display summary table with sparkline chart
st.dataframe(
    summary_df,
    column_config={
        "First month trend": st.column_config.LineChartColumn(
            "First month trend",
            help=f"Weekly values from {first_date.date()} to {first_month['Date'].max().date()}",
        )
    },
    hide_index=True,
    use_container_width=True,
)

# Display raw dataset in expander
with st.expander("Show raw imported data"):
    st.dataframe(df, use_container_width=True)