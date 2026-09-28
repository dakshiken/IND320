import pandas as pd
import streamlit as st

#path to CSV file
csv_path = "data/D2Dbook/data/reservoirs.csv"


@st.cache_data  #cache data for speed
def load_data() -> pd.DataFrame:
    """load, clean, and convert reservoir data to englsiih."""
    df = pd.read_csv(csv_path)

    #filter for national data only
    df = df[(df["omrType"] == "NO") & (df["omrnr"] == 0)]

    #rename columns to english
    df = df.rename(
        columns={
            "dato_Id": "Date",
            "fyllingsgrad": "Fill Degree",
            "kapasitet_TWh": "Capacity (TWh)",
            "fylling_TWh": "Fill Volume (TWh)",
            "fyllingsgrad_forrige_uke": "Fill Degree Previous Week",
            "endring_fyllingsgrad": "Change in Fill Degree",
        }
    )

    df["Date"] = pd.to_datetime(df["Date"])  #convert to datetime
    df = df[
        [
            "Date",
            "Fill Degree",
            "Capacity (TWh)",
            "Fill Volume (TWh)",
            "Fill Degree Previous Week",
            "Change in Fill Degree",
        ]
    ]

    return df.sort_values("Date").reset_index(drop=True)