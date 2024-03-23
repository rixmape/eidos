import firebase_admin
import streamlit as st
from firebase_admin import credentials, firestore


class SurveyForm:
    def __init__(self, state):
        self.state = state
        self.options = [
            "Strongly Disagree",
            "Disagree",
            "Agree",
            "Strongly Agree",
        ]
        self.feedback = {}
        self.is_sent = False

        self.initialize_feedback_database()

    def initialize_feedback_database(self, database_name="user_feedback"):
        if not firebase_admin._apps:
            certificate = dict(st.secrets["firebase"])
            credential = credentials.Certificate(certificate)
            firebase_admin.initialize_app(credential)

        firestore_client = firestore.client()
        self.database = firestore_client.collection(database_name)

    def handle_likert_questions(self):
        self.feedback["likert-scale"] = []
        for question in self.state.config.survey["likert-scale"]:
            st.markdown(f"#### {question}")
            col, _ = st.columns(2)
            answer = col.select_slider(
                question,
                self.options,
                key=question,
                value=self.options[-1],
                label_visibility="collapsed",
            )
            self.feedback["likert-scale"].append(
                {"question": question, "answer": answer}
            )

    def handle_open_questions(self):
        self.feedback["open-ended"] = []
        for question in self.state.config.survey["open-ended"]:
            st.markdown(f"#### {question}")
            answer = st.text_area(
                question,
                key=question,
                height=100,
                max_chars=500,
                label_visibility="collapsed",
            )
            self.feedback["open-ended"].append(
                {"question": question, "answer": answer}
            )

    def send_feedback(self):
        st.divider()
        if st.button("Send Feedback"):
            messages = self.state.chatbot.get_chat_messages()
            self.feedback["messages"] = messages
            self.feedback["timestamp"] = firestore.SERVER_TIMESTAMP

            self.database.add(self.feedback)
            self.is_sent = True
            st.rerun()

    def run(self):
        self.handle_likert_questions()
        self.handle_open_questions()

        if self.is_sent:
            st.success("Feedback sent successfully!")
            return

        self.send_feedback()
