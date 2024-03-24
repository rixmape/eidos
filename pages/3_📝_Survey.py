import streamlit as st

from eidos.survey import SurveyForm
from helpers import page_utils


class SurveyPage:
    def __init__(self):
        self.initialize_session_state()
        self.initialize_page()

    def initialize_session_state(self):
        self.state = st.session_state
        self.state.setdefault("survey_form", None)

    def initialize_page(self):
        custom_style = """
        div[role="radiogroup"] {
            grid-template-columns: repeat(1, 1fr) !important;
        }
        """
        page_utils.initialize_page(
            "📝",
            "Share your experience",
            custom_style=custom_style,
        )

    def run_survey_form(self):
        if not self.state.survey_form:
            self.state.survey_form = SurveyForm(self.state)
        self.state.survey_form.run()

    def run(self):
        self.run_survey_form()


if __name__ == "__main__":
    survey_page = SurveyPage()
    survey_page.run()
