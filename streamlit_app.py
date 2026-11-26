import streamlit as st

from modules import guide, state
from modules.menu import GROUPS
from modules.theme import COPPER, GROUP_COLORS

st.set_page_config(
    page_title="IND320", page_icon=":material/water_medium:", layout="wide",
    menu_items={
        "Get help": "https://github.com/dakshiken/IND320",
        "Report a bug": "https://github.com/dakshiken/IND320/issues",
        "About": "**IND320: Water, Weather and Power**  \nProject work at NMBU. Data: NVE Magasinstatistikk, Open-Meteo (ERA5), ENTSO-E (via MongoDB) and Norges Bank.",
    },
)
state.init()

# menu: home page plus one section per group
home_page = st.Page("views/home.py", title="Home", icon=":material/home:", default=True)
menu = {group: [st.Page(file, title=title, icon=icon, url_path=title.lower().replace(" ", "-")) for file, title, icon, *_ in pages]
        for group, pages in GROUPS.items()}
page = st.navigation({"": [home_page], **menu})
order = [home_page] + [p for pages in menu.values() for p in pages]          # for previous / next

# group colour on the title line and the active menu item
color = next((GROUP_COLORS[g] for g, pages in menu.items() if page in pages), COPPER)
st.markdown(
    f"<style>h1{{border-bottom:4px solid {color};padding-bottom:.25rem}}"
    f"[data-testid='stSidebarNav'] a[aria-current='page']{{border-left:4px solid {color}}}</style>",
    unsafe_allow_html=True,
)

# the sidebar summary is filled after the page has run, so it shows the latest choice
with st.sidebar:
    summary = st.container()
try:
    page.run()
finally:                       # runs also when a page calls st.stop()
    guide.footer(order, page)
    with summary:
        st.markdown("**Your choice**")
        st.caption(f":material/location_on: Area: **{state.area()}**")
        if state.period():
            st.caption(f":material/calendar_month: Time frame: **{state.period()[0]} to {state.period()[1]}**")
        if page != home_page:
            st.page_link(home_page, label="Change on the Home page", icon=":material/map:")
