import streamlit as st

from chatbot import ChatbotAgent
from switch_page import switch_page

st.set_page_config(page_title="Chat", page_icon="🧐")
st.title("🧐 Hello, I'm Eidos!")

style = """
<style>
div[data-testid="stChatMessage"] {
    gap: 1rem !important;
}
</style>
"""
st.markdown(style, unsafe_allow_html=True)

st.session_state.setdefault("config", None)
if not st.session_state.config:
    switch_page("configuration")

st.session_state.setdefault("chatbot", None)
if not st.session_state.chatbot:
    st.session_state.chatbot = ChatbotAgent(st.session_state.config)
st.session_state.chatbot.run()
