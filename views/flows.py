import calendar

import plotly.express as px
import streamlit as st

from modules import app_data, guide, state
from modules.mongo import get_flows, get_options, get_totals
from modules.theme import COPPER, SLATE, style

st.title(":material/swap_horiz: Cross-border flows")
guide.intro(
    "How much electric power flows between Norway and its neighbours, hour by hour? The data comes from ENTSO-E and is stored in MongoDB.",
    [
        "Choose a **connection** (a link between two areas or countries). The list starts with a connection of the price area you chose on Home "
        "(for example EL 3 = NO3). For water areas and Norway it starts with the first connection.",
        "The **pie chart** shows how much power went out of Norway and into Norway on that connection during the year (in GWh).",
        "The **line plots** show the flow hour by hour for the months you pick (click a month to select or remove it). "
        "There is one panel for every connection, and the connection you chose is in bold.",
        "**MW** (megawatt) is how much power flows at one moment, **GWh** (gigawatt-hour) is the energy over a period. "
        "More *smoothing* gives a calmer line that is easier to read.",
    ],
    uses=("area",),
)

# connections and years in the database
try:
    connections, years = get_options()
except Exception as e:
    app_data.stop_on_error(e, "MongoDB", "Check the MONGO_URI secret and that Atlas allows connections from this app.")
if not connections:
    st.warning("The database has no flow data yet.")
    st.stop()

names = {"out": "Out of Norway", "in": "Into Norway"}
colors = {"out": COPPER, "in": SLATE}        # same colours in both charts

left, right = st.columns(2)

# pie chart: total flow in and out for one connection and year
with left:
    st.subheader("Total flow in one year")
    zone = state.zone()                                   # NO1-NO5 if a price area is chosen
    first = next((i for i, c in enumerate(connections) if zone and zone in c), 0)
    connection = st.radio("Connection", connections, index=first, help="A link between two areas or countries. It starts with a connection of the area from Home.")
    year = st.selectbox("Year", years, index=max(len(years) - 2, 0), help="Used by both charts. The default is the last complete year.")
    totals = get_totals(connection, year)
    directions = [d for d in ("out", "in") if d in totals]
    if directions:
        fig = px.pie(names=[names[d] for d in directions], values=[totals[d] for d in directions], color=[names[d] for d in directions],
                     color_discrete_map={names[d]: colors[d] for d in directions}, hole=0.35)
        fig.update_traces(texttemplate="%{label}<br>%{value:,.0f} GWh<br>(%{percent})", textposition="outside")
        st.plotly_chart(style(fig, f"{connection}, {year}: total flow in and out of Norway", height=420), theme=None)
    else:
        st.warning("No data for this connection and year.")

# line plot for the chosen months: one panel per connection, one line per direction
with right:
    st.subheader(f"Flow in {year}")
    month_names = list(calendar.month_abbr)[1:]
    chosen = st.pills("Months", month_names, selection_mode="multi", default=["Jan"], wrap=True, help="Click to select or remove months. Months that are not next to each other are shown with a gap.")
    if not chosen:
        st.info("Select at least one month.")
    else:
        try:
            flows = get_flows(year, tuple(month_names.index(m) + 1 for m in chosen))
        except Exception as e:
            app_data.stop_on_error(e, "MongoDB", "No flow data for these months.")
        hours = st.select_slider("Smoothing (rolling mean in hours, 1 = off)", [1, 6, 24, 72, 168], value=24,
                                 help="Each point is the average of this many hours. 24 = one day, 168 = one week.")
        data = flows.rolling(hours, center=True, min_periods=1).mean()
        long = data.rename_axis("time").melt(ignore_index=False, value_name="MW").reset_index()      # time, connection, direction, MW
        fig = px.line(long, x="time", y="MW", color="direction", facet_col="connection", facet_col_wrap=3,
                      color_discrete_map=colors, labels={"direction": "Direction"})
        # chosen connection in bold, English legend names
        fig.for_each_annotation(lambda a: a.update(text=f"<b>{a.text.split('=')[-1]}</b>" if a.text.split("=")[-1] == connection else a.text.split("=")[-1]))
        fig.for_each_trace(lambda t: t.update(name=names.get(t.name, t.name)))
        st.plotly_chart(style(fig, f"{', '.join(chosen)} {year}", height=230 * -(-len(connections) // 3) + 120), theme=None)

with st.expander("About the data"):
    st.markdown(
        """
- **Where:** ENTSO-E Transparency Platform, physical cross-border flows, fetched with the entsoe-py library
  for each Norwegian bidding zone and its neighbours, in both directions (out of Norway and into Norway).
- **Period:** hourly values from 1 January two years back until the last run of the notebook.
- **Pipeline:** Jupyter notebook -> Cassandra -> extracted with Spark -> MongoDB (time stamps in UTC, shown in Norwegian time).
- **Pie chart:** the hourly MW values summed over the year = MWh, shown in GWh.
        """
    )
