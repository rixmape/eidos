import streamlit as st
import yaml

from helpers import page_utils

st.session_state.visited_home = True

page_utils.initialize_page("🏠", "Learn philosophy with Eidos")

with open("config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
    st.markdown(config["welcome_message"])

st.divider()
next_page = "pages/1_✨_Configuration.py"
st.page_link(next_page, label="✨ Configure your experience")
