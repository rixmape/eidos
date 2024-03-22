import firebase_admin
import streamlit as st
from firebase_admin import credentials, firestore

from helpers import page_utils


class SurveyPage:
    def __init__(self):
        self.state = st.session_state
        self.state.setdefault("feedback", [])
        self.initialize_page()
        self.initialize_feedback_database()

        self.options = [
            "Strongly Agree",
            "Agree",
            "Disagree",
            "Strongly Disagree",
        ]

    def initialize_page(self):
        page_utils.initialize_page(
            "📝",
            "Share your experience",
            customize_style=False,
        )

    def initialize_feedback_database(self, database_name="user_feedback"):
        if not firebase_admin._apps:
            certificate = dict(st.secrets["firebase"])
            credential = credentials.Certificate(certificate)
            firebase_admin.initialize_app(credential)

        firestore_client = firestore.client()
        self.database = firestore_client.collection(database_name)

    def handle_likert_questions(self):
        for question in self.state.config.survey["likert-scale"]:
            st.markdown(f"#### {question}")
            value = st.radio(
                question,
                self.options,
                key=question,
                label_visibility="collapsed",
            )
            self.state.feedback.append(
                {
                    "question": question,
                    "value": value,
                }
            )

    def handle_open_questions(self):
        for question in self.state.config.survey["open-ended"]:
            st.markdown(f"#### {question}")
            value = st.text_area(
                question,
                key=question,
                height=100,
                max_chars=500,
                label_visibility="collapsed",
            )
            self.state.feedback.append(
                {
                    "question": question,
                    "value": value,
                }
            )

    def send_feedback(self):
        if st.button("Send Feedback"):
            self.database.add(
                {
                    "feedback": self.state.feedback,
                    "timestamp": firestore.SERVER_TIMESTAMP,
                }
            )
            st.success("Feedback sent successfully!")

    def run(self):
        self.handle_likert_questions()
        self.handle_open_questions()
        st.divider()
        self.send_feedback()


if __name__ == "__main__":
    survey_page = SurveyPage()
    survey_page.run()
