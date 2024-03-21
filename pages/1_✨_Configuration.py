import streamlit as st

from eidos.configuration import Configuration
from helpers.switch_page import switch_page

st.set_page_config(page_title="Configuration", page_icon="✨")
st.title("✨ Let's customize your experience!")

style = """
<style>
div[data-testid="stButton"] {
    text-align: right;
}
label[data-baseweb="radio"] {
    border: 1px solid rgb(50, 50, 50) !important;
    padding: 1rem 1rem;
    border-radius: 0.5rem;
    margin: 0;
    width: 100%;
    height: 100%;
}
label:has(.st-aw) {
    background-color: rgb(93, 50, 50);
}
label:has(.st-aw) * {
    color: white;
}
div[role="radiogroup"] {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
}
</style>
"""
st.markdown(style, unsafe_allow_html=True)

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
