# Generated from notebooks/project_work_part4.ipynb, edit the notebook instead
import pandas as pd
import requests


def download_rates(start, end, currencies=("EUR", "USD")):
    # one request for all currencies (EXR = exchange rates, B = business days, SP = spot)
    url = f"https://data.norges-bank.no/api/data/EXR/B.{'+'.join(currencies)}.NOK.SP"
    r = requests.get(url, params={"format": "sdmx-json", "startPeriod": start, "endPeriod": end}, timeout=60)
    r.raise_for_status()
    data = r.json()
    data = data.get("data", data)   # sometimes wrapped in "data"
    # series dimensions tell the currency, the observation dimension gives the dates
    dims = data["structure"]["dimensions"]["series"]
    dates = [v["id"] for v in data["structure"]["dimensions"]["observation"][0]["values"]]
    pos = [d["id"] for d in dims].index("BASE_CUR")
    rates = {}
    for key, series in data["dataSets"][0]["series"].items():
        currency = dims[pos]["values"][int(key.split(":")[pos])]["id"]
        rates[f"{currency}/NOK"] = pd.Series({dates[int(i)]: float(obs[0]) for i, obs in series["observations"].items()})
    df = pd.DataFrame(rates)
    df.index = pd.to_datetime(df.index)
    df.index.name = "Date"
    return df.sort_index()
