import streamlit as st

from eidos.chatbot import ChatbotAgent
from helpers.page_handling import switch_page, set_page_style

st.set_page_config(page_title="Chat", page_icon="🧐")
st.title("🧐 Hello, I'm Eidos!")
set_page_style()

st.session_state.setdefault("visited_home", False)
if not st.session_state.visited_home:
    switch_page("main")

st.session_state.setdefault("chatbot", None)
if not st.session_state.chatbot:
    st.session_state.chatbot = ChatbotAgent(st.session_state.config)
st.session_state.chatbot.run()
