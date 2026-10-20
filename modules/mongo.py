import os

import pandas as pd
import streamlit as st
from pymongo import MongoClient
from pymongo.server_api import ServerApi


def _uri() -> str:
    #Connection string from Streamlit secrets
    try:
        return st.secrets["MONGO_URI"]
    except Exception:
        uri = os.getenv("MONGO_URI")
        if not uri:
            raise RuntimeError("MONGO_URI is missing: add it to .streamlit/secrets.toml or to the app's Secrets")
        return uri


@st.cache_resource
def get_collection():
#one shared MongoDB connection for the whole app.
    client = MongoClient(_uri(), server_api=ServerApi("1"), serverSelectionTimeoutMS=10000)
    return client["ind320"]["crossborder_flows"]


@st.cache_data(ttl=3600)
def get_options():
#connections and years that exist in the database.
    collection = get_collection()
    return sorted(collection.distinct("connection")), sorted(collection.distinct("year"))


@st.cache_data(ttl=3600)
def get_totals(connection, year) -> dict:
#total flow in GWh per direction
    docs = get_collection().find({"connection": connection, "year": year}, {"_id": 0, "direction": 1, "mw": 1})
    totals = {}
    for d in docs:
        totals[d["direction"]] = totals.get(d["direction"], 0.0) + sum(d["mw"]) / 1000
    return totals


@st.cache_data(ttl=3600)
def get_flows(year, months) -> pd.DataFrame:
    """hourly flow in the chosen months, one column per, norsk local time as index.
    hgours outside the chosen months are NaN, so a line plot breaks between months that are not next to each other."""
    docs = get_collection().find({"year": year, "month": {"$in": list(months)}},
                                 {"_id": 0, "connection": 1, "direction": 1, "ts": 1, "mw": 1})
    rows = [(d["connection"], d["direction"], t, v) for d in docs for t, v in zip(d["ts"], d["mw"])]
    df = pd.DataFrame(rows, columns=["connection", "direction", "ts", "mw"])
    wide = df.pivot_table(index="ts", columns=["connection", "direction"], values="mw")   # ts is UTC
    wide = wide.reindex(pd.date_range(wide.index.min(), wide.index.max(), freq="h"))
    wide.index = wide.index.tz_localize("UTC").tz_convert("Europe/Oslo").tz_localize(None)
    return wide