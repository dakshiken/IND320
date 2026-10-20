#loads the nve reservoir statistics directly from the NVE API (replaces the CSV file)
import pandas as pd
import requests
import streamlit as st

BASE = "https://biapi.nve.no/magasinstatistikk/api/Magasinstatistikk"

# norsk to english names
RENAME = {
    "dato_Id": "Date",
    "omrType": "Area Type",
    "omrnr": "Area Number",
    "fyllingsgrad": "Fill Degree",
    "kapasitet_TWh": "Capacity (TWh)",
    "fylling_TWh": "Fill Volume (TWh)",
    "fyllingsgrad_forrige_uke": "Fill Degree Previous Week",
    "endring_fyllingsgrad": "Change in Fill Degree",
}
VALUE_COLS = ["Fill Degree", "Capacity (TWh)", "Fill Volume (TWh)",
              "Fill Degree Previous Week", "Change in Fill Degree"]
AREA_TYPES = ["EL", "NO", "VASS"]   # bidding zones, whole country, watercourse areas


@st.cache_data(ttl=3600, show_spinner="Downloading data from the NVE API ...")
def download_all() -> pd.DataFrame:
    """Download the full history for all areas once (the API has no date parameters). Cached for one hour."""
    resp = requests.get(f"{BASE}/HentOffentligData", timeout=60)
    resp.raise_for_status()
    df = pd.DataFrame(resp.json()).rename(columns=RENAME)
    df["Date"] = pd.to_datetime(df["Date"])
    #label per area
    df["Area"] = (df["Area Type"] + " " + df["Area Number"].astype(str)).replace({"NO 0": "Norway"})
    columns = ["Date", "Area Type", "Area Number", "Area"] + VALUE_COLS
    return df[columns].sort_values(["Area Type", "Area Number", "Date"]).reset_index(drop=True)

# data for one area type and a download interval
def load_data(area_type=None, start=None, end=None) -> pd.DataFrame:

    df = download_all()
    if area_type is not None:
        df = df[df["Area Type"] == area_type]
    month = df["Date"].dt.to_period("M").astype(str)
    keep = pd.Series(True, index=df.index)
    if start is not None:
        keep &= month >= start
    if end is not None:
        keep &= month <= end
    return df[keep]