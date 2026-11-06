# Generated from notebooks/project_work_part3.ipynb: change the notebook, not this file
import json
import random

import pandas as pd
import requests


def download_weather(region, start, end, n_points=20,
                     variables=("temperature_2m", "precipitation", "rain", "snowfall", "wind_speed_10m", "wind_gusts_10m")):
    points = random.Random(0).sample(json.load(open("data/sample_points.json"))[region], n_points)
    frames = []
    # batch in chunks of 10
    for i in range(0, n_points, 10):                                 
        batch = points[i:i + 10]
        r = requests.get("https://archive-api.open-meteo.com/v1/archive", timeout=120, params={
            "latitude": ",".join(str(lat) for lon, lat in batch), "longitude": ",".join(str(lon) for lon, lat in batch),
            "start_date": start, "end_date": end, "hourly": ",".join(variables), "models": "era5"})
        if r.status_code != 200:
            raise RuntimeError(r.json()["reason"])
        data = r.json()
        # handle single vs multi response format
        for loc in data if isinstance(data, list) else [data]:   
            frames.append(pd.DataFrame(loc["hourly"]).set_index("time").rename(columns=lambda c: c.removesuffix("_era5")))
    # mean across all sampled points
    weather = pd.concat(frames).groupby(level=0).mean() 
    weather.index = pd.to_datetime(weather.index)
    return weather
