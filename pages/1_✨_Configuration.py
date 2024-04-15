import streamlit as st

from eidos.configuration import Configuration
from helpers import page_utils


class ConfigurationPage:
    def __init__(self):
        self.initialize_session_state()
        self.initialize_page()

    def initialize_session_state(self):
        self.state = st.session_state
        self.state.setdefault("config", None)

    def initialize_page(self):
        page_utils.initialize_page("✨", "Personalize your experience")

    def run_configuration(self):
        if not self.state.config:
            self.state.config = Configuration()
        self.state.config.run()

    def display_next_page_link(self):
        st.divider()
        st.page_link("pages/2_🤖_Chat.py", label="🤖 Ready to Chat")

    def run(self):
        self.run_configuration()
        self.display_next_page_link()


if __name__ == "__main__":
    config_page = ConfigurationPage()
    config_page.run()
