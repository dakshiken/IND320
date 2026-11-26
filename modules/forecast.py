# Generated from notebooks/project_work_part4.ipynb, edit the notebook instead
import time

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from river import linear_model, optim, preprocessing, time_series

from modules.theme import COPPER, SAGE, SLATE, style


def to_oslo(df):
    # UTC time stamps -> Norwegian time
    out = df.copy()
    out.index = out.index.tz_localize("UTC").tz_convert("Europe/Oslo").tz_localize(None)
    return out


def weekly_extra(weather=None, rates=None, flows=None):
    # all sources on one weekly index (weeks end on Sunday, like the NVE dates)
    parts = []
    if weather is not None:
        parts.append(to_oslo(weather).resample("W-SUN").mean())          # hourly UTC -> Oslo -> week
    if rates is not None:
        parts.append(rates.resample("W-SUN").mean().ffill())             # business days -> week, gaps filled forward
    if flows is not None:
        parts.append(flows.resample("W-SUN").mean())                     # hourly, already Oslo time
    return pd.concat(parts, axis=1)


def forecast_fill(fill, extra=None, exog=(), origin=None, horizon=26, history=260,
                  p=2, d=0, q=1, m=52, sp=1, sd=0, sq=0, lr=0.05, epochs=10,
                  future="seasonal", interval=False, quantiles=(0.1, 0.9), interval_epochs=20):
    # SNARIMAX forecast of the weekly fill degree for one region
    # fill: weekly series, extra: weekly table of all sources, exog: columns of extra to use
    exog = list(exog)
    data = fill.interpolate().to_frame("y")
    if exog:
        data = data.join(extra[exog].reindex(data.index, method="nearest", tolerance=pd.Timedelta("3D")))
    origin = data.index[-1] if origin is None else pd.Timestamp(origin)
    # train on the last `history` weeks before the origin, complete rows only
    train = data.loc[:origin].dropna().tail(history)
    if len(train) < max(30, 2 * (p + q)):
        raise ValueError(f"only {len(train)} weeks of training data, too few for this model")
    dates = pd.date_range(train.index[-1] + pd.Timedelta(weeks=1), periods=horizon, freq="7D")

    # exog values for the horizon: real ones ("actual", back-test only) or the mean of the same week in the training data
    weeks = train.index.isocalendar().week.values
    seasonal = train[exog].groupby(weeks).mean() if exog else None
    xs = []
    for t in dates:
        row = {}
        for c in exog:
            real = data[c].get(t, np.nan) if future == "actual" else np.nan
            week = t.isocalendar().week
            row[c] = real if pd.notna(real) else (seasonal.loc[week, c] if week in seasonal.index else train[c].mean())
        xs.append(row)
    rows = list(zip(train["y"].values, [dict(zip(exog, v)) for v in train[exog].to_numpy()]))

    def fit_forecast(loss=None, passes=epochs):
        # learns one week at a time; a few passes over the history help
        reg = linear_model.LinearRegression(optimizer=optim.SGD(lr), intercept_lr=lr, **({"loss": loss} if loss else {}))
        model = time_series.SNARIMAX(p=p, d=d, q=q, m=m, sp=sp, sd=sd, sq=sq, regressor=preprocessing.StandardScaler() | reg)
        for _ in range(passes):
            for y, x in rows:
                model.learn_one(y, x)
        return np.array(model.forecast(horizon, xs=xs))      # dynamic: each step uses the earlier forecasts

    t0 = time.time()
    top = max(1, fill.max())
    result = pd.DataFrame({"forecast": np.clip(fit_forecast(), 0, top)}, index=dates)
    if interval:
        # one model per quantile: lower and upper limit
        low, high = (np.clip(fit_forecast(optim.losses.Quantile(a), interval_epochs), 0, top) for a in quantiles)
        result["lower"] = np.minimum(low, result["forecast"])
        result["upper"] = np.maximum(high, result["forecast"])
    result["actual"] = fill.reindex(dates)
    err = (result["forecast"] - result["actual"]).abs().dropna()
    return result, {"mae": err.mean() if len(err) else np.nan, "n_train": len(train), "seconds": time.time() - t0,
                    "train_start": train.index[0], "train_end": train.index[-1]}


def forecast_plot(fill, result, weeks_before=104, animate=True):
    # history, forecast (animated, grows week by week) and optional interval
    first = result.index[0]
    past = fill[first - pd.Timedelta(weeks=weeks_before): first - pd.Timedelta(days=1)]
    dates = list(result.index)
    has_band = "lower" in result
    color = COPPER

    def band(k):          # interval as a polygon over the first k weeks
        if not has_band:
            return go.Scatter(x=[], y=[])
        x = dates[:k] + dates[:k][::-1]
        y = list(result["upper"][:k]) + list(result["lower"][:k])[::-1]
        return go.Scatter(x=x, y=y, fill="toself", mode="none", fillcolor="rgba(227,147,95,0.25)", name="Interval", hoverinfo="skip")

    def line(k):
        return go.Scatter(x=dates[:k], y=result["forecast"][:k], mode="lines+markers", name="Forecast", line=dict(color=color), marker=dict(size=5))

    fig = go.Figure([
        go.Scatter(x=past.index, y=past.values, mode="lines", name="Observed (history)", line=dict(color=SLATE)),
        go.Scatter(x=dates, y=result["actual"], mode="lines", name="Observed (forecast period)", line=dict(color=SAGE, dash="dot")),
        band(len(dates)), line(len(dates))])
    if animate:
        fig.frames = [go.Frame(name=str(k), data=[band(k), line(k)], traces=[2, 3]) for k in range(1, len(dates) + 1)]
        fig.update_layout(
            updatemenus=[dict(type="buttons", direction="left", x=0, y=-0.15, showactive=False, buttons=[
                dict(label="▶ Play", method="animate", args=[None, {"frame": {"duration": 150, "redraw": True}, "fromcurrent": True}]),
                dict(label="⏸ Pause", method="animate", args=[[None], {"frame": {"duration": 0}, "mode": "immediate"}])])],
            sliders=[dict(x=0.15, len=0.85, y=-0.1, currentvalue=dict(prefix="Weeks ahead: "), steps=[
                dict(label=str(k), method="animate", args=[[str(k)], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"}])
                for k in range(1, len(dates) + 1)])])
    # fixed axes, no jumping while it plays
    values = np.concatenate([past.values, result.to_numpy().ravel()])
    values = values[~np.isnan(values)]
    pad = 0.05 * (values.max() - values.min())
    fig.update_yaxes(range=[values.min() - pad, values.max() + pad], title_text="Fill degree")
    fig.update_xaxes(range=[past.index[0] if len(past) else first, dates[-1]])
    return style(fig, "Forecast of the fill degree")
