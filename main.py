import streamlit as st

from helpers import page_utils


class HomePage:
    def __init__(self):
        self.initialize_session_state()
        self.initialize_page()

    def initialize_session_state(self):
        self.state = st.session_state
        self.state.visited_home = True

    def initialize_page(self):
        page_utils.initialize_page("🏠", "Welcome!")

    def display_welcome_message(self):
        st.header(":red[Eidos] is your philosophy companion.")
        st.image("images/eidos_cycle.png")

    def display_next_page_link(self):
        st.divider()
        if st.button("✨ Start Using Eidos!"):
            page_utils.navigate_to_page("configuration")

    def run(self):
        self.display_welcome_message()
        self.display_next_page_link()


if __name__ == "__main__":
    home_page = HomePage()
    home_page.run()
