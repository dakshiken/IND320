import streamlit as st
import random


# Configure page settings
st.set_page_config(
    page_title="IND320", page_icon="💧", layout="wide"
)

# Sidebar info
st.sidebar.title("Navigation")
st.sidebar.info(
    "Use the pages above to explore the other pages:\n\n"
    "- **Page 2** — data loader\n"
    "- **Page 3** — time series plot\n"
    "- **Page 4** — test content"
)

# Main page title and intro
st.title("💧IND320💧")
st.markdown(
    """
    Use the sidebar to navigate between pages.
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