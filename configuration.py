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

    def make_selection(self, prompt, options):
        st.markdown(f"#### {prompt}")
        selected_option = st.radio(
            prompt,
            options,
            format_func=lambda map: map["title"].capitalize(),
            captions=[option["caption"] for option in options],
            horizontal=True,
            label_visibility="collapsed",
        )
        return selected_option

    def run(self):
        self.selected_topic = self.make_selection(
            "What do you want to talk about?",
            self.topics,
        )
        self.selected_language_style = self.make_selection(
            "How do you want me to respond?",
            self.language_styles,
        )
        self.selected_dialogue_pace = self.make_selection(
            "Which dialogue pace do you prefer?",
            self.dialogue_paces,
        )
