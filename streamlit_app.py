import streamlit as st

# page configuration (each page file can set its own as well)
st.set_page_config(page_title="IND320", page_icon="💧", layout="wide")

# group -> (icon, data source, [(page file, title, icon), ...])
MENU = {
    "Reservoirs": ("💧", "NVE Magasinstatistikk API", [
        ("pages/Page_2.py", "Reservoir table", "📊"),
        ("pages/Page_3.py", "Reservoir plot", "📈"),
        ("pages/Page_4.py", "STL and spectrogram", "🌊"),
    ]),
    "Weather": ("🌦️", "Open-Meteo API", [
        ("pages/Page_5.py", "Outliers and anomalies", "🌦️"),
    ]),
    "Energy flows": ("⚡", "ENTSO-E data in MongoDB", [
        ("pages/Page_6.py", "Cross-border flows", "💦"),
    ]),
}

# every file becomes an st.Page, and the built-in menu is hidden
home = st.Page("pages/Page_1.py", title="Home", icon="🏠", default=True)
groups = {g: [st.Page(f, title=t, icon=i) for f, t, i in items] for g, (_, _, items) in MENU.items()}
pg = st.navigation([home] + [p for items in groups.values() for p in items], position="hidden")


def nav_button(page):
    # one button per page, the current page is highlighted
    if st.button(page.title, icon=page.icon, key=page.title, width="stretch",
                 type="primary" if page.title == pg.title else "secondary"):
        st.switch_page(page)


# our own sidebar: title, home button, one expander per group
with st.sidebar:
    st.title("💧 IND320")
    nav_button(home)
    for group, (icon, source, _) in MENU.items():
        with st.expander(f"{icon} {group}", expanded=True):
            st.caption(source)
            for page in groups[group]:
                nav_button(page)
    st.divider()
    st.caption("[GitHub](https://github.com/dakshiken/IND320) · [Streamlit app](https://ind320-dakshi.streamlit.app)")

pg.run()   # run the chosen page