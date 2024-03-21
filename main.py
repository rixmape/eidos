import streamlit as st

from helpers import page_handling

st.set_page_config(page_title="Welcome to Eidos!", page_icon="🏠")
st.title("🏠 Welcome to Eidos!")

page_handling.set_page_style()

st.session_state.visited_home = True

st.page_link(
    "pages/1_✨_Configuration.py",
    label="✨ Start configuring your experience",
)
