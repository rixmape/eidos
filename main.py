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
        page_utils.initialize_page("🏠", "Welcome!")

    def load_config(self):
        with open("config.yaml", "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    def display_welcome_message(self):
        st.header(":red[Eidos] is a philosophy companion.")
        st.image("images/eidos_cycle.png")

    def display_credentials_input(self):
        st.markdown("#### What is your name?")
        name = st.text_input(
            "Full Name",
            placeholder="First Middle Last (e.g., Juan R. Dela Cruz)",
            label_visibility="collapsed",
        )

        st.markdown("#### Enter password given by your teacher.")
        password = st.text_input(
            "Password",
            type="password",
            label_visibility="collapsed",
        )

        if st.button("✨ Start Using Eidos!"):
            if name and password:
                st.session_state.name = name
                if password in st.secrets["auth"]["passwords"]:
                    st.session_state.password = password
                    page_utils.navigate_to_page("configuration")
                else:
                    st.error("Invalid password. Try again.")
            else:
                st.error("Please fill in all fields.")

    def run(self):
        self.display_welcome_message()
        self.display_credentials_input()


if __name__ == "__main__":
    home_page = HomePage()
    home_page.run()
