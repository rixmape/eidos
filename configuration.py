import os
import streamlit as st


class Configuration:
    def __init__(self):
        self.load_environment_variables()
        self.load_parameters()
        self.load_messages()

    def load_environment_variables(self):
        environment_variables = st.secrets["env"]
        for key, value in environment_variables.items():
            os.environ[key] = value

    def load_messages(self):
        self.messages = st.secrets["messages"]

    def load_parameters(self):
        self.parameters = st.secrets["parameters"]

    def apply_custom_styles(self):
        custom_style = """
        <style>
        h4 {
            padding: 2rem 0 1rem 0;
        }
        label[data-baseweb="radio"] {
            border: 1px solid rgb(50, 50, 50) !important;
            padding: 1rem 1rem;
            border-radius: 0.5rem;
            margin: 0;
            width: 100%;
            height: 100%;
        }
        label:has(.st-aw) {
            background-color: rgb(93, 50, 50);
        }
        label:has(.st-aw) * {
            color: white;
        }
        div[role="radiogroup"] {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
        }
        </style>
        """
        st.markdown(custom_style, unsafe_allow_html=True)

    def make_selection(self, prompt, secret_key):
        st.markdown(f"#### {prompt}")
        options = st.secrets[secret_key]
        selected_option = st.radio(
            prompt,
            options.keys(),
            format_func=lambda key: key.title(),
            captions=options.values(),
            horizontal=True,
            label_visibility="collapsed",
        )
        return options[selected_option]

    def save_configuration(self):
        *_, column = st.columns(4)
        if column.button(
            "Save Configuration",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.is_configured = True
            st.rerun()

    def run(self):
        self.apply_custom_styles()

        intro_text = (
            "Let's customize your experience. Answer a few questions to"
            " tailor our discussions to your preferences."
        )
        st.markdown(f"#### {intro_text}")

        self.topic = self.make_selection(
            "What do you want to talk about?",
            "topics",
        )
        self.language_style = self.make_selection(
            "How do you want me to respond?",
            "language_styles",
        )
        self.dialogue_pace = self.make_selection(
            "Which dialogue pace do you prefer?",
            "dialogue_paces",
        )

        st.divider()
        self.save_configuration()
