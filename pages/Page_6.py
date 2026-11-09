from modules.mongo import get_flows, get_options, get_totals
import calendar

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import streamlit as st
# page configuration
st.set_page_config(page_title="Cross-border flows", page_icon="💦", layout="wide")
st.title("💦  Cross-border flows 💦")
st.markdown("Hourly physical flows (MW) between Norway and its neighbours, read from MongoDB.")

# connections and years that exist in the database
try:
    connections, years = get_options()
except Exception as e:
    st.error(f"Could not read from MongoDB: {e}")
    st.stop()

names = {"out": "Out of Norway", "in": "Into Norway"}
colors = {"out": "#ff0000", "in": "#0084ff"}        # same colour per direction in both charts

left, right = st.columns(2)

# pie chart of the total flow in and out of Norway for one connection and year
with left:
    st.subheader("Total flow in one year")
    connection = st.radio("Connection", connections)
    year = st.selectbox("Year", years, index=max(len(years) - 2, 0))   # last complete year
    totals = get_totals(connection, year)
    directions = [d for d in ("out", "in") if d in totals]
    if directions:
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.pie([totals[d] for d in directions],
               labels=[f"{names[d]}\n{totals[d]:,.0f} GWh" for d in directions],
               colors=[colors[d] for d in directions], autopct="%1.1f%%", startangle=90)
        ax.set_title(f"{connection}, {year}: total flow in and out of Norway")
        st.pyplot(fig)
    else:
        st.warning("No data for this connection and year.")

# line plot for any set of months of the chosen year: one panel per connection, one line per direction
with right:
    st.subheader(f"Flow in {year}")
    month_names = list(calendar.month_abbr)[1:]
    chosen = st.pills("Months", month_names, selection_mode="multi", default=["Jan"], wrap=True)
    if not chosen:
        st.info("Select at least one month.")
    else:
        flows = get_flows(year, tuple(month_names.index(m) + 1 for m in chosen))
        hours = st.select_slider("Smoothing (rolling mean in hours, 1 = off)", [1, 6, 24, 72, 168], value=24)
        data = flows.rolling(hours, center=True, min_periods=1).mean()
        rows = -(-len(connections) // 3)                      # three panels per row
        fig, axes = plt.subplots(rows, 3, figsize=(8, 2.4 * rows + 0.6), sharex=True, sharey=True,
                                 squeeze=False, layout="constrained")
        for ax, conn in zip(axes.flat, connections):
            for direction in ("out", "in"):
                if (conn, direction) in data.columns:
                    ax.plot(data.index, data[(conn, direction)], color=colors[direction], label=names[direction], linewidth=1)
            ax.set_title(conn, fontsize=9, fontweight="bold" if conn == connection else "normal")   # chosen connection in bold
            ax.tick_params(labelsize=7)
        for ax in axes.flat[len(connections):]:
            ax.axis("off")
        locator = mdates.AutoDateLocator(maxticks=4)
        axes.flat[0].xaxis.set_major_locator(locator)
        axes.flat[0].xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        fig.supylabel("Flow (MW)", fontsize=9)
        fig.suptitle(f"{', '.join(chosen)} {year}", fontsize=10)
        fig.legend(*axes.flat[0].get_legend_handles_labels(), loc="outside lower center", ncol=2, fontsize=8)
        st.pyplot(fig)

#documentation of the data source
with st.expander("About the data"):
    st.markdown(
        """
- **where:** entsoe transparency platform, physical cross border flows, fetched with the entsoe-py library
  for each norwegian bidding zone and its neighbours, in both directions , out of Norway and into norway.
- **Period:** hourly values from 1 january 2024 until the last run of the notebook.
- **Pipeline:** jupyter notebook -> cassandra -> extracted with Spark -> mongodb
- **Pie chart:** the hourly MW values summed over the year = MWh, shown in GWh.
        """
    )