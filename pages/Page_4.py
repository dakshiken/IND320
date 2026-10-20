import calendar

import matplotlib.pyplot as plt
import streamlit as st

from modules.mongo import get_flows, get_options, get_totals

#oage configuration
st.set_page_config(page_title="Cross-border flows", page_icon="💦", layout="wide")
st.title("💦  Cross-border flows 💦")
st.markdown("Hourly physical flows (MW) between Norway and its neighbours, read from MongoDB.")

#connections and years that exist in the database
try:
    connections, years = get_options()
except Exception as e:
    st.error(f"Could not read from MongoDB: {e}")
    st.stop()

left, right = st.columns(2)

#pie chart of the total flow in and out of Norway for one connection and year
with left:
    st.subheader("Total flow in one year")
    connection = st.radio("Connection", connections)
    year = st.selectbox("Year", years, index=max(len(years) - 2, 0))   # last complete year
    totals = get_totals(connection, year)
    names = {"out": "Out of Norway", "in": "Into Norway"}
    directions = [d for d in ("out", "in") if d in totals]
    if directions:
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.pie([totals[d] for d in directions],
               labels=[f"{names[d]}\n{totals[d]:,.0f} GWh" for d in directions],
               autopct="%1.1f%%", startangle=90)
        ax.set_title(f"{connection}, {year}: total flow in and out of Norway")
        st.pyplot(fig)
    else:
        st.warning("No data for this connection and year.")

# line plot for any set of months of the chosen year, one line per connection and direction
with right:
    st.subheader(f"Hourly flow in {year}")
    month_names = list(calendar.month_abbr)[1:]
    chosen = st.pills("Months", month_names, selection_mode="multi", default=["Jan"])
    if not chosen:
        st.info("Select at least one month.")
    else:
        flows = get_flows(year, tuple(month_names.index(m) + 1 for m in chosen))
        colors = {c: f"C{i}" for i, c in enumerate(connections)}
        fig, ax = plt.subplots(figsize=(8, 5))
        for conn, direction in flows.columns:
            #solid = out of Norway, dashed = into Norway
            ax.plot(flows.index, flows[(conn, direction)], color=colors[conn],
                    linestyle="-" if direction == "out" else "--",
                    linewidth=2.5 if conn == connection else 0.8, label=f"{conn} ({direction})")
        ax.set_ylabel("Flow (MW)")
        ax.set_title(f"{', '.join(chosen)} {year} (thick = {connection})")
        ax.legend(fontsize=7, ncol=2, loc="upper left", bbox_to_anchor=(1.01, 1))
        fig.autofmt_xdate()
        st.pyplot(fig)

#documentation of the data source
with st.expander("About the data"):
    st.markdown(
        """
- **where:** ENTSO-E transparency platform, physical cross border flows, fetched with the entsoe-py library
  for each norwegian bidding zone and its neighbours, in both directions , out of Norway and into Norway.
- **Period:** hourly values from 1 January 2024 until the last run of the notebook.
- **Pipeline:** jupyter notebook -> cassandra -> extracted with Spark -> mongodb
- **Pie chart:** the hourly MW values summed over the year = MWh, shown in GWh.
        """
    )