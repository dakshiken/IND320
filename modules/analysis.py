# Generated from notebooks/project_work_part4.ipynb, edit the notebook instead
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.fft import dct, idct
from scipy.signal import spectrogram
from sklearn.neighbors import LocalOutlierFactor
from statsmodels.tsa.seasonal import STL

from modules.theme import ALERT, COPPER, MUTED, SEQUENTIAL, SLATE, style


def spc_outliers(series, cutoff=0.03, n_std=3.0, label="value"):
    x = series.interpolate().bfill().ffill()
    # DCT high-pass: zero the low frequencies
    coef = dct(x.values, norm="ortho")
    coef[: int(cutoff * 2 * len(x) / 24)] = 0
    satv = idct(coef, norm="ortho")                           # seasonally adjusted variation (SATV)
    centre = np.median(satv)
    sigma = 1.4826 * np.median(np.abs(satv - centre))        # robust std (MAD)
    out = np.abs(satv - centre) > n_std * sigma
    mid = x.values - satv + centre                           # slow part: limits follow the season
    limit = dict(color=MUTED, dash="dash", width=1)
    fig = go.Figure()
    fig.add_scatter(x=x.index, y=x.values, mode="lines", name=label, line=dict(width=1))
    fig.add_scatter(x=x.index, y=mid + n_std * sigma, mode="lines", name=f"Limits ({n_std:g} robust std)", line=limit)
    fig.add_scatter(x=x.index, y=mid - n_std * sigma, mode="lines", showlegend=False, line=limit)
    fig.add_scatter(x=x.index[out], y=x.values[out], mode="markers", name="Outliers", marker=dict(color=ALERT, size=5))
    fig.update_yaxes(title_text=label)
    return style(fig), {"n": len(x), "outliers": int(out.sum()), "share": out.mean(), "robust_std": sigma,
                        "table": x[out].to_frame(label)}


def lof_anomalies(series, contamination=0.01, n_neighbors=20, label="value"):
    x = series.interpolate().bfill().ffill()
    # value in std units, time scaled to 0-20, so both count for the neighbours
    points = np.c_[(x.values - x.mean()) / x.std(), np.linspace(0, 20, len(x))]
    lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
    flag = lof.fit_predict(points) == -1                      # -1 = anomaly
    fig = go.Figure()
    fig.add_scatter(x=x.index, y=x.values, mode="lines", name=label, line=dict(width=1))
    fig.add_scatter(x=x.index[flag], y=x.values[flag], mode="markers", name="Anomalies", marker=dict(color=ALERT, size=6))
    fig.update_yaxes(title_text=label)
    table = pd.DataFrame({label: x[flag], "LOF score": -lof.negative_outlier_factor_[flag]}).sort_values("LOF score", ascending=False)
    return style(fig), {"n": len(x), "anomalies": int(flag.sum()), "share": flag.mean(), "table": table}


def stl_plot(series, seasonal=13, trend=105, robust=True):
    # STL on a regular weekly grid, one panel per component
    res = STL(series.asfreq("7D").interpolate(), period=52, seasonal=seasonal, trend=trend, robust=robust).fit()
    parts = {"Observed": res.observed, "Trend": res.trend, "Seasonal": res.seasonal, "Residual": res.resid}
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.03)
    for i, (name, part) in enumerate(parts.items(), start=1):
        fig.add_scatter(x=part.index, y=part.values, mode="lines", name=name, showlegend=False, line=dict(width=1), row=i, col=1)
        fig.update_yaxes(title_text=name, row=i, col=1)
    return style(fig, f"STL: seasonal={seasonal}, trend={trend}, robust={robust}", height=650)


def spectrogram_plot(series, window=156, overlap=78):
    f, t, power = spectrogram(series.interpolate().values, fs=52, nperseg=window, noverlap=overlap)   # 52 samples per year
    keep = f <= 6                                              # 0-6 cycles per year
    fig = go.Figure(go.Heatmap(x=series.index[0].year + t, y=f[keep], z=10 * np.log10(power[keep]),
                               colorscale=SEQUENTIAL, zsmooth="best", colorbar=dict(title="Power (dB)")))
    fig.update_layout(xaxis_title="Year", yaxis_title="Frequency (cycles per year)")
    return style(fig, f"Window {window} weeks, overlap {overlap} weeks")


def sliding_correlation(x, y, lag=0, window=52):
    # x at week t against y at t + lag (positive lag: x first); weekly series
    y = y.dropna()
    x = x.reindex(y.index, method="nearest", tolerance=pd.Timedelta("3D"))    # match weeks, 3 days apart at most
    shifted = y.shift(-lag)
    rolling = x.rolling(window, center=True).corr(shifted)             # correlation in a sliding window
    cross = pd.Series({k: x.corr(y.shift(-k)) for k in range(-26, 27)})  # every lag
    ahead = cross[cross.index >= 0]                                     # weather first = usable for forecasting
    best = ahead.abs().idxmax()
    z = lambda s: (s - s.mean()) / s.std()
    fig = make_subplots(rows=3, cols=1, vertical_spacing=0.1, subplot_titles=(
        f"Standardised series ({y.name} moved {lag} weeks)", f"Sliding window correlation ({window} weeks)", "Correlation at every lag (whole period)"))
    fig.add_scatter(x=x.index, y=z(x), name=str(x.name), mode="lines", line=dict(width=1), row=1, col=1)
    fig.add_scatter(x=x.index, y=z(shifted), name=f"{y.name} (lag {lag})", mode="lines", line=dict(width=1), row=1, col=1)
    fig.add_scatter(x=rolling.index, y=rolling, name="Sliding correlation", mode="lines", line=dict(color=COPPER), row=2, col=1)
    fig.add_hline(y=0, line_dash="dot", line_color=MUTED, row=2, col=1)
    fig.add_bar(x=cross.index, y=cross.values, name="Correlation", showlegend=False, row=3, col=1,
                marker_color=[COPPER if k == lag else SLATE for k in cross.index])
    fig.update_xaxes(title_text="Lag (weeks)", row=3, col=1)
    fig.update_yaxes(range=[-1, 1], row=2, col=1)
    fig.update_yaxes(range=[-1, 1], row=3, col=1)
    fig.update_layout(legend_y=1.05)                                    # room for the first subplot title
    return style(fig, height=800), {"overall": x.corr(shifted), "best_lag": int(best), "best_corr": cross[best], "rolling": rolling}
