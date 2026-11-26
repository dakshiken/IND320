# Generated from notebooks/project_work_part4.ipynb, edit the notebook instead
import json
import random
import time

import pandas as pd
import requests


def download_weather(region, start, end, n_points=50,
                     variables=("temperature_2m", "precipitation", "rain", "snowfall", "wind_speed_10m", "wind_gusts_10m")):
    # same random points every time (file from part 3)
    points = random.Random(0).sample(json.load(open("data/sample_points.json"))[region], n_points)
    frames = []
    # max 10 points per request
    for i in range(0, n_points, 10):
        batch = points[i:i + 10]
        params = {"latitude": ",".join(str(lat) for lon, lat in batch), "longitude": ",".join(str(lon) for lon, lat in batch),
                  "start_date": start, "end_date": end, "hourly": ",".join(variables), "models": "era5"}
        for attempt in range(3):
            r = requests.get("https://archive-api.open-meteo.com/v1/archive", params=params, timeout=120)
            if r.status_code != 429:
                break
            time.sleep(60)             # rate limit (600 calls/min): wait, retry
        if r.status_code != 200:
            raise RuntimeError(r.json().get("reason", r.text[:200]))
        data = r.json()
        # one point gives a dict, several give a list
        for loc in data if isinstance(data, list) else [data]:
            frames.append(pd.DataFrame(loc["hourly"]).set_index("time").rename(columns=lambda c: c.removesuffix("_era5")))
    # mean over the points
    weather = pd.concat(frames).groupby(level=0).mean()
    weather.index = pd.to_datetime(weather.index)
    return weather
