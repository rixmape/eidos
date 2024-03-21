import streamlit as st

from eidos.configuration import Configuration
from helpers.page_handling import switch_page, set_page_style

st.set_page_config(page_title="Configuration", page_icon="✨")
st.title("✨ Let's customize your experience!")
set_page_style()

st.session_state.setdefault("visited_home", False)
if not st.session_state.visited_home:
    switch_page("main")

st.session_state.config = Configuration()
st.session_state.config.run()

st.page_link(
    "pages/2_🧐_Chat.py",
    label="Chat",
    icon="🧐",
)
