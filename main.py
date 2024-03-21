import streamlit as st

from helpers import page_utils

st.session_state.visited_home = True

page_utils.initialize_page("🏠", "Welcome!")

st.divider()
next_page_name = "pages/1_✨_Configuration.py"
st.page_link(next_page_name, label="✨ Configure your experience")
