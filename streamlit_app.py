import streamlit as st
import random


#configure page settings
st.set_page_config(page_title="IND320", page_icon="💧", layout="wide")

#sidebar info
st.sidebar.title("Navigation")
st.sidebar.info(
    "Use the pages above to explore the other pages:\n\n"
    "- **Page 2** — reservoir table (NVE API)\n"
    "- **Page 3** — reservoir plot (NVE API)\n"
    "- **Page 4** — STL and spectrogram (NVE API)\n"
    "- **Page 5** — weather outliers and anomalies (Open-Meteo API)\n"
    "- **Page 6** — cross-border flows (MongoDB)"
)

#main page title and intro
st.title("💧IND320💧")
st.markdown(
    """
    Use the sidebar to navigate between pages.

    links to git and this app:
    - https://ind320-dakshi.streamlit.app
    - https://github.com/dakshiken/IND320
    
    """
)

#falling emojis using injected CSS animation

emoji = "Welcome 👋"
count = random.randint(3, 15)
spans = "".join(
    f'<span class="e" style="left:{random.randint(5, 95)}%; animation-delay:{random.uniform(0, 1):.1f}s">{emoji}</span>'
    for _ in range(count)
)

st.markdown(
    f"<style>@keyframes d{{to{{top:100vh;opacity:0}}}}.e{{position:fixed;top:0;font-size:36px;animation:d 3s forwards}}</style>{spans}",
    unsafe_allow_html=True,
)