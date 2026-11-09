# Generated from notebooks/project_work_part3.ipynb: change the notebook, not this file
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from scipy.fft import dct, idct
from scipy.signal import spectrogram
from sklearn.neighbors import LocalOutlierFactor
from statsmodels.tsa.seasonal import STL


def spc_outliers(series, cutoff=0.03, n_std=3.0, label="value"):
  x = series.interpolate()
  coef = dct(x.values, norm="ortho")
  # zero out low frequencies for high-pass filter
  coef[: int(cutoff * 2 * len(x) / 24)] = 0
  satv = idct(coef, norm="ortho")
  centre = np.median(satv)
  # robust std via mad
  sigma = 1.4826 * np.median(np.abs(satv - centre))
  # find points outside bounds
  out = np.abs(satv - centre) > n_std * sigma
  # dynamic baseline for limits
  mid = x.values - satv + centre

  fig = Figure(figsize=(10, 4))
  ax = fig.subplots()
  ax.plot(x.index, x, lw=0.6, label=label)
  ax.plot(
      x.index,
      mid + n_std * sigma,
      "k--",
      lw=1,
      label=f"Limits ({n_std:g} robust std)",)
  ax.plot(x.index, mid - n_std * sigma, "k--", lw=1)
  ax.scatter(
      x.index[out], x[out], s=8, color="red", zorder=3, label="Outliers")
  ax.set_ylabel(label)
  ax.legend(loc="upper right")

  return fig, {
      "n": len(x),
      "outliers": out.sum(),
      "share": out.mean(),
      "robust_std": sigma,
      "table": x[out].to_frame(label),}


def lof_anomalies(series, contamination=0.01, n_neighbors=20, label="value"):
  x = series.interpolate()

  # value in std units, time scaled to 20 units
  points = np.c_[(x.values - x.mean()) / x.std(), np.linspace(0, 20, len(x))]

  lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
  flag = lof.fit_predict(points) == -1  # -1 = anomaly

  fig = Figure(figsize=(10, 4))
  ax = fig.subplots()
  ax.plot(x.index, x, lw=0.6, label=label)
  ax.scatter(x.index[flag], x[flag], s=10, color="red", zorder=3, label="Anomalies")
  ax.set_ylabel(label)
  ax.legend(loc="upper right")

  table = pd.DataFrame({
      label: x[flag],
      "LOF score": -lof.negative_outlier_factor_[flag],
  }).sort_values("LOF score", ascending=False)

  return fig, {
      "n": len(x),
      "anomalies": flag.sum(),
      "share": flag.mean(),
      "table": table,}


def stl_plot(series, seasonal=13, trend=105, robust=True):
  # stl decomposition on a regular weekly grid with gap interpolation
  res = STL(
      series.asfreq("7D").interpolate(),
      period=52,
      seasonal=seasonal,
      trend=trend,
      robust=robust,
  ).fit()
  fig = Figure(figsize=(10, 7), layout="constrained")
  parts = {
      "Observed": res.observed,
      "Trend": res.trend,
      "Seasonal": res.seasonal,
      "Residual": res.resid,}
  # one subplot per component
  for ax, (name, part) in zip(fig.subplots(4, 1, sharex=True), parts.items()):
    ax.plot(part, lw=0.8)
    ax.set_ylabel(name)
    fig.suptitle(f"STL: seasonal={seasonal}, trend={trend}, robust={robust}")
  return fig


def spectrogram_plot(series, window=156, overlap=78):
    f, t, power = spectrogram(series.interpolate().values, fs=52, nperseg=window, noverlap=overlap)    # fs = 52 weeks per year
    fig = Figure(figsize=(10, 4), layout="constrained")
    ax = fig.subplots()
    # convert time array to years and plot pcolormesh
    mesh = ax.pcolormesh(series.index[0].year + t, f, 10 * np.log10(power), shading="gouraud")         # t in years
    ax.set_ylim(0, 6)
    ax.set(xlabel="Year", ylabel="Frequency (cycles per year)", title=f"Window {window} weeks, overlap {overlap} weeks")
    fig.colorbar(mesh, ax=ax, label="Power (dB)")
    return fig
