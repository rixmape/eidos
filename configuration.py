import os

import streamlit as st


class Configuration:
    def __init__(self):
        self.load_env_variables()
        self.params = st.secrets["params"]
        self.messages = st.secrets["messages"]

    def load_env_variables(self):
        """Load environment variables from Streamlit secrets file."""
        env_variables = st.secrets["env"]
        for key, val in env_variables.items():
            os.environ[key] = val

    def run(self):
        st.subheader(self.messages["welcome"])

        self.set_style()
        self.topic = self.handle_selection(
            "What do you want to talk about?",
            "topics",
        )
        self.language_style = self.handle_selection(
            "How do you want me to respond?",
            "language_styles",
        )
        self.dialogue_pace = self.handle_selection(
            "Which dialogue pace do you prefer?",
            "dialogue_paces",
        )
        self.handle_saving()

    def set_style(self):
        style = """
        <style>
        h3 {
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
        st.markdown(style, unsafe_allow_html=True)

    def handle_selection(self, label, secret_key):
        st.subheader(label)
        options = st.secrets[secret_key]
        choice = st.radio(
            label,
            options.keys(),
            format_func=lambda key: key.title(),
            captions=options.values(),
            horizontal=True,
            label_visibility="collapsed",
        )
        return options[choice]

    def handle_saving(self):
        st.divider()
        *_, col = st.columns(4)
        if col.button(
            "Save Configuration",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.is_configured = True
            st.rerun()
