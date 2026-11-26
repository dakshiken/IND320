"""Colours for the whole app. The same values are in .streamlit/config.toml, so Streamlit and Plotly match."""
import plotly.graph_objects as go
import plotly.io as pio

# base: warm graphite with glaze colours
BG, PANEL, GRID = "#171514", "#211E1C", "#34302C"
TEXT, MUTED = "#EEE7DC", "#A39B90"

COPPER, SLATE, SAND = "#E3935F", "#86A9D6", "#E8D08C"
ROSE, SAGE, LILAC = "#DB8DA6", "#A3C4A4", "#AE9FD9"
ALERT = "#FF6159"          # outliers and anomalies
HIGHLIGHT = "#5FB8F2"      # outline of the selected area on the map

COLORWAY = [COPPER, SLATE, SAND, ROSE, SAGE, LILAC]
GROUP_COLORS = {"Status": SAGE, "Patterns": SLATE, "Outlook": ROSE}
SEQUENTIAL = [[0, "#3B2F45"], [0.4, "#8E3E5C"], [0.7, COPPER], [1, "#F7E7B0"]]      # low to high (map, heatmap)

_t = go.layout.Template(pio.templates["plotly_dark"])
_t.layout.update(
    colorway=COLORWAY,
    font=dict(family="Source Sans Pro, sans-serif", color=TEXT),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor=PANEL,
    xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID),
    yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hoverlabel=dict(bgcolor=BG, font_color=TEXT, bordercolor=GRID),
    margin=dict(l=10, r=10, t=50, b=10),
    updatemenudefaults=dict(bgcolor=GRID, bordercolor=MUTED, font=dict(color=TEXT)),     # Play / Pause buttons
    sliderdefaults=dict(bgcolor=GRID, activebgcolor=COPPER, bordercolor=GRID, tickcolor=MUTED, font=dict(color=MUTED)),
)
pio.templates["ind320"] = _t


def style(fig, title=None, height=None):
    """Apply the app template to a figure."""
    fig.update_layout(template="ind320", title=title, height=height)
    return fig
