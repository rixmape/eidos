import streamlit as st

from eidos.configuration import Configuration
from helpers import page_utils

page_utils.initialize_page("✨", "Configure your experience")

st.session_state.config = Configuration()
st.session_state.config.run()

st.divider()
next_page_name = "pages/2_🧐_Chat.py"
st.page_link(next_page_name, label="🧐 Start chatting")
