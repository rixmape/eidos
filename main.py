import streamlit as st

from chatbot import ChatbotAgent
from configuration import Configuration

if __name__ == "__main__":
    st.set_page_config(page_title="Eidos", page_icon="🧐")

    state = st.session_state
    state.setdefault("is_configured", False)
    state.setdefault("chatbot", None)

    if not state.is_configured:
        state.config = Configuration()
        state.config.run()
    else:
        if not state.chatbot:
            state.chatbot = ChatbotAgent(state.config)
        state.chatbot.run()
