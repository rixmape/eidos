import streamlit as st

from eidos.configuration import Configuration
from helpers import page_handling

st.set_page_config(page_title="Configuration", page_icon="✨")
st.title("✨ Let's customize your experience!")

page_handling.go_to_homepage_at_refresh()
page_handling.set_page_style()

st.session_state.config = Configuration()
st.session_state.config.run()

st.page_link(
    "pages/2_🧐_Chat.py",
    label="🧐 Start chatting",
)
