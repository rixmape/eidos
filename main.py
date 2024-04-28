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
        st.header("Examine your beliefs with :red[Eidos].")
        st.image("images/eidos_cycle.png")

        tab1, tab2 = st.tabs(["Description", "Demo"])

        with tab1:
            st.markdown("### ⭐ What is Eidos?")
            st.markdown(
                """
                <p style="font-size: 1.3rem">Eidos is a chatbot that facilitates dialogues to explore and refine your beliefs.</p>
                <p style="font-size: 1rem;color: rgb(152, 152, 152)">Using the Socratic method, Eidos encourages critical thinking and introspection. It identifies inconsistencies, such as logical fallacies and contradictions, in your responses. Eidos integrates a database of philosophical texts to ground the dialogue in accurate and reliable information.
                """,
                unsafe_allow_html=True,
            )

        with tab2:
            st.markdown("### 🎮 How to Use Eidos?")
            st.video("https://youtu.be/p_OaXf-eCws")

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
