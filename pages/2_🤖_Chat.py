import streamlit as st
from eidos.chatbot import ChatbotAgent
from helpers import page_utils


class ChatPage:
    def __init__(self):
        self.initialize_session_state()
        self.initialize_page()

    def initialize_session_state(self):
        self.state = st.session_state
        self.state.setdefault("chatbot", None)

    def initialize_page(self):
        page_utils.initialize_page("🤖", "Hello, I'm Eidos!")

    def run_chatbot(self):
        if not self.state.chatbot:
            self.state.chatbot = ChatbotAgent(self.state.config)
        self.state.chatbot.run()

    def display_next_page_link(self):
        if (
            self.state.chatbot.prompt_count
            >= self.state.config.parameters["min_prompt_count"]
        ):
            st.divider()
            next_page = "pages/3_📝_Survey.py"
            st.page_link(next_page, label="💬 Answer survey form")

    def run(self):
        self.run_chatbot()
        self.display_next_page_link()


if __name__ == "__main__":
    chat_page = ChatPage()
    chat_page.run()
