import streamlit as st

from eidos.chatbot import ChatbotAgent
from helpers import page_utils

page_utils.initialize_page("🧐", "Hello, I'm Eidos!")

state = st.session_state
state.setdefault("chatbot", None)

if not state.chatbot:
    state.chatbot = ChatbotAgent(state.config)

state.chatbot.run()

if state.chatbot.prompt_count >= state.config.parameters["min_prompt_count"]:
    st.divider()
    next_page = "pages/3_📝_Survey.py"
    st.page_link(next_page, label="💬 Answer survey form")
