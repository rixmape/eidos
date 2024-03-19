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
        self.set_style()
        self.handle_topic()
        self.handle_language_style()
        self.handle_dialogue_pace()
        self.handle_document_upload()
        self.handle_saving()

    def set_style(self):
        style = """
        <style>
        label[data-baseweb="radio"] {
            border: 1px solid gray;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            margin: 0;
            width: 100%;
        }
        div[role="radiogroup"] {
            display: flex;
            justify-content: space-between;
            flex-wrap: nowrap;
            gap: 1rem;
        }
        </style>
        """
        st.markdown(style, unsafe_allow_html=True)

    def handle_topic(self):
        label = "Conversation Topic"
        st.subheader(label)
        topics = st.secrets["topics"]
        choice = st.radio(
            label,
            topics,
            format_func=lambda key: key.title(),
            horizontal=True,
            label_visibility="collapsed",
        )
        self.topic = topics[choice]

    def handle_language_style(self):
        label = "Language Style"
        st.subheader(label)
        styles = st.secrets["language_styles"]
        choice = st.radio(
            label,
            styles,
            format_func=lambda key: key.title(),
            horizontal=True,
            label_visibility="collapsed",
        )
        self.language_style = styles[choice]

    def handle_dialogue_pace(self):
        label = "Dialogue Pace"
        st.subheader(label)
        paces = st.secrets["dialogue_paces"]
        choice = st.radio(
            label,
            paces,
            format_func=lambda key: key.title(),
            horizontal=True,
            label_visibility="collapsed",
        )
        self.dialogue_pace = paces[choice]

    def handle_document_upload(self):
        label = "Upload Documents"
        st.subheader(label)
        self.docs = st.file_uploader(
            label,
            type=["txt"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )

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
