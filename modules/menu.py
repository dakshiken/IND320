"""The pages in three groups: (file, menu name, icon, short text, choices from Home that the page starts with).
The front page is views/home.py."""

CHIPS = {"area": ":material/location_on: area", "area type": ":material/location_on: area type", "time frame": ":material/calendar_month: time frame"}

GROUPS = {
    "Status": [
        ("views/reservoirs.py", "Reservoirs", ":material/water_medium:", "How full are the reservoirs? Weekly numbers as a table with small lines, and as a plot (NVE)", ("area type", "time frame")),
        ("views/flows.py", "Cross-border flows", ":material/swap_horiz:", "How much power flows between Norway and its neighbours, hour by hour (ENTSO-E)", ("area",)),
        ("views/exchange_rates.py", "Exchange rates", ":material/currency_exchange:", "What one euro or one US dollar costs in Norwegian kroner (Norges Bank)", ("time frame",)),
    ],
    "Patterns": [
        ("views/seasonality.py", "Seasonality", ":material/waves:", "Does the fill degree repeat a pattern every year? STL decomposition and spectrogram", ("area",)),
        ("views/weather_anomalies.py", "Weather anomalies", ":material/thunderstorm:", "Find unusual weather: outliers (SPC) and anomalies (LOF) in hourly weather (Open-Meteo)", ("area",)),
        ("views/correlation.py", "Correlation", ":material/scatter_plot:", "Do the weather and the reservoirs move together? Sliding window correlation with lag", ("area",)),
    ],
    "Outlook": [
        ("views/forecast.py", "Forecast", ":material/auto_graph:", "Forecast the fill degree for the coming weeks, with weather, exchange rates and flows as extra data (SNARIMAX)", ("area", "time frame")),
    ],
}


def uses_text(uses):
    return " · ".join(CHIPS[u] for u in uses)
