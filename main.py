import streamlit as st
import yaml

from helpers import page_utils


class HomePage:
    def __init__(self):
        self.initialize_session_state()
        self.initialize_page()
        self.load_config()

    def initialize_session_state(self):
        self.state = st.session_state
        self.state.visited_home = True

    def initialize_page(self):
        page_utils.initialize_page("🏠", "Learn philosophy with Eidos")

    def load_config(self):
        with open("config.yaml", "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    def display_welcome_message(self):
        st.markdown(self.config["welcome_message"])

    def display_next_page_link(self):
        st.divider()
        next_page = "pages/1_✨_Configuration.py"
        st.page_link(next_page, label="✨ Configure your experience")

    def run(self):
        self.display_welcome_message()
        self.display_next_page_link()


if __name__ == "__main__":
    home_page = HomePage()
    home_page.run()
