import matplotlib.pyplot as plt
import streamlit as st

from modules.data_loader import load_data

# Page configuration
st.set_page_config(page_title="Data Plot", page_icon="📈", layout="wide")

# Page title
st.title("📈 Data Plot")

# Load cached data
df = load_data()

# Get numeric value columns
value_cols = [c for c in df.columns if c != "Date"]

# UI layout for filter controls
col1, col2 = st.columns([1, 2])

with col1:
    # Dropdown for column selection
    column_choice = st.selectbox("Column to plot", options=["All columns"] + value_cols)

with col2:
    # Slider for month range (defaults to first month)
    month_labels = sorted(df["Date"].dt.to_period("M").astype(str).unique())
    start_month, end_month = st.select_slider(
        "Month range", options=month_labels, value=(month_labels[0], month_labels[0])
    )

# Filter dataset by selected month range
month_str = df["Date"].dt.to_period("M").astype(str)
plot_df = df.loc[month_str.between(start_month, end_month)].set_index("Date")

# Create plot figure
fig, ax = plt.subplots(figsize=(10, 5))

if column_choice == "All columns":
    # Plot all normalized columns (0-1 scale)
    normalized = (plot_df - plot_df.min()) / (plot_df.max() - plot_df.min())
    for col in value_cols:
        ax.plot(normalized.index, normalized[col], label=col, linewidth=1.2)
    ax.set_ylabel("Normalised value (0-1)")
    ax.legend(fontsize=8, loc="upper left")
    title = "All columns (min-max normalised)"
else:
    # Plot single selected column
    ax.plot(plot_df.index, plot_df[column_choice], color="tab:blue", linewidth=1.5)
    ax.set_ylabel(column_choice)
    title = column_choice

# Format plot title, labels, and grid
ax.set_title(f"Norwegian national reservoir series — {title}\n({start_month} to {end_month})")
ax.set_xlabel("Date")
ax.grid(alpha=0.3)
fig.autofmt_xdate()
fig.tight_layout()

# Render plot and caption in Streamlit
st.pyplot(fig)
st.caption(f"Showing {len(plot_df)} weekly observations between {start_month} and {end_month}.")