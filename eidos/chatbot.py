from operator import itemgetter

import streamlit as st
from langchain_community.chat_message_histories.streamlit import (
    StreamlitChatMessageHistory,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableParallel
from langchain_openai import ChatOpenAI

from eidos.document_manager import DocumentManager


class ChatbotPipeline:
    def __init__(self, configuration):
        self.config = configuration
        self.document_manager = DocumentManager(configuration)

        self.initialize_llms()
        self.initialize_templates()

        self.chain_query_expansion = self.create_chain_query_expansion()
        self.chain_context = self.create_chain_context()
        self.chain_answer = self.create_chain_answer()
        self.chain_complete = self.create_chain_complete()

    def initialize_llms(self):
        self.llm_main = ChatOpenAI(model=self.config.parameters["llm_main"])
        self.llm_helper = ChatOpenAI(model=self.config.parameters["llm_helper"])

    def initialize_templates(self):
        instructions = [
            self.config.selected_topic["instruction"].strip(),
            self.config.selected_language_style["instruction"].strip(),
        ]

        template = self.config.templates["system"]
        self.system_template = template.format(
            additional_instructions=" ".join(instructions)
        )

        template = self.config.templates["answer"]
        self.answer_template = template.format(
            additional_instructions=" ".join(instructions)
        )

    def create_chain_query_expansion(self):
        system_template = self.config.templates["query_expansion"]
        human_template = "{question}"
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", system_template),
                MessagesPlaceholder(variable_name="history"),
                ("human", human_template),
            ]
        )
        return prompt_template | self.llm_helper | StrOutputParser()

    def create_chain_answer(self):
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_template),
                MessagesPlaceholder(variable_name="history"),
                ("human", self.answer_template),
            ]
        )
        return prompt_template | self.llm_main | StrOutputParser()

    def create_chain_context(self):
        chain_context = (
            {
                "question": itemgetter("question"),
                "history": itemgetter("history"),
            }
            | self.chain_query_expansion
            | self.document_manager.retriever
            | self.format_documents
        )

        return chain_context

    def create_chain_complete(self):
        return RunnableParallel(
            question=itemgetter("question"),
            history=itemgetter("history"),
            context=self.chain_context,
        ).assign(answer=self.chain_answer)

    def format_documents(self, docs):
        return "\n\n".join([f"'''\n{doc.page_content}\n'''" for doc in docs])

    def get_response(self, question, history):
        return self.chain_complete.invoke(
            {
                "question": question,
                "history": history.messages,
            }
        )


class ChatbotAgent:
    def __init__(self, configuration):
        self.config = configuration
        self.pipeline = ChatbotPipeline(configuration)
        self.chat_history = StreamlitChatMessageHistory()
        self.prompt_count = 0

        if not self.chat_history.messages:
            self.add_greeting()

    def add_greeting(self):
        greeting = self.config.templates["greeting"]
        self.chat_history.add_ai_message(greeting)

    def display_messages(self):
        for message in self.chat_history.messages:
            st.chat_message(message.type).markdown(message.content)

    def handle_input(self):
        if query := st.chat_input(key="chat_input"):
            st.chat_message("human").write(query)
            response = self.pipeline.get_response(query, self.chat_history)
            answer = response["answer"]
            st.chat_message("ai").write(answer)

            self.chat_history.add_user_message(query)
            self.chat_history.add_ai_message(answer)
            self.prompt_count += 1
            st.rerun()

    def check_prompt_limit(self):
        if self.prompt_count >= self.config.parameters["max_prompt_count"]:
            message = (
                "You have reached the limit."
                " Please answer the survey form now."
            )
            st.warning(message, icon="⚠️")
            return True
        return False

    def display_info_message(self):
        if len(self.chat_history.messages) == 1:
            st.info(self.config.tips["first_message"], icon="ℹ️")

    def run(self):
        self.display_messages()

        if self.check_prompt_limit():
            return

        self.handle_input()
        self.display_info_message()
