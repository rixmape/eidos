import os

import streamlit as st
import yaml


class Configuration:
    def __init__(self):
        self.load_config_file()
        self.load_environment_variables()

    def load_environment_variables(self):
        environment_variables = st.secrets["env"]
        for key, value in environment_variables.items():
            os.environ[key] = value

    def load_config_file(self, path="config.yaml"):
        with open(path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)

        for key, value in config.items():
            setattr(self, key, value)

    def apply_custom_styles(self):
        custom_style = """
        <style>
        h4,
        div[data-testid="stExpander"] {
            padding: 2rem 0 1rem 0;
        }
        div[data-testid="stButton"] {
            padding: 1rem 0 0;
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

    def make_selection(self, prompt, options):
        st.markdown(f"#### {prompt}")
        value = st.radio(
            prompt,
            list(options.keys()),
            format_func=lambda key: key.capitalize(),
            captions=[options[key]["caption"] for key in options.keys()],
            horizontal=True,
            label_visibility="collapsed",
        )
        return options[value]["instruction"]

    def custom_input(self, prompt):
        value = st.text_area(
            prompt,
            max_chars=250,
            key=prompt.lower(),
            height=150,
        )
        return value

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
            "What do you want to talk about?", self.topics
        )
        self.language_style = self.make_selection(
            "How do you want me to respond?",
            self.language_styles,
        )
        self.dialogue_pace = self.make_selection(
            "Which dialogue pace do you prefer?",
            self.dialogue_paces,
        )

        with st.expander("Advanced Configuration"):
            self.user_info = self.custom_input(
                "What can you tell me about yourself?",
            )

        self.save_configuration()
