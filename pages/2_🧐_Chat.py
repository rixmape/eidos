import streamlit as st

from eidos.chatbot import ChatbotAgent
from helpers import page_handling

st.set_page_config(page_title="Chat", page_icon="🧐")
st.title("🧐 Hello, I'm Eidos!")

page_handling.go_to_homepage_at_refresh()
page_handling.set_page_style()

st.session_state.setdefault("chatbot", None)
if not st.session_state.chatbot:
    st.session_state.chatbot = ChatbotAgent(st.session_state.config)
st.session_state.chatbot.run()
