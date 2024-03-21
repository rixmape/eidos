import streamlit as st

from eidos.chatbot import ChatbotAgent
from helpers import page_utils

page_utils.initialize_page("🧐", "Hello, I'm Eidos!")

st.session_state.setdefault("chatbot", None)
if not st.session_state.chatbot:
    st.session_state.chatbot = ChatbotAgent(st.session_state.config)
st.session_state.chatbot.run()

st.divider()
next_page = "pages/3_📝_Survey.py"
st.page_link(next_page, label="💬 Answer survey form")
