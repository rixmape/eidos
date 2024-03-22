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
        self.initialize_main_instruction()

        self.chain_query_expansion = self.create_chain_query_expansion()
        self.chain_with_documents = self.create_chain_with_documents()

    def initialize_llms(self):
        self.llm_main = ChatOpenAI(model=self.config.parameters["llm_main"])
        self.llm_helper = ChatOpenAI(model=self.config.parameters["llm_helper"])

    def initialize_main_instruction(self):
        messages = [
            self.config.templates["role"],
            self.config.selected_topic["instruction"],
            self.config.selected_language_style["instruction"],
            self.config.selected_dialogue_pace["instruction"],
        ]

        self.main_instruction = "\n".join(messages)

    def create_chain_query_expansion(self):
        system_template = self.main_instruction
        human_template = self.config.templates["query_expansion"]
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", system_template),
                MessagesPlaceholder(variable_name="history"),
                ("human", human_template),
            ]
        )
        return prompt_template | self.llm_helper | StrOutputParser()

    def create_chain_with_documents(self):
        chain_context = (
            {
                "question": itemgetter("question"),
                "history": itemgetter("history"),
            }
            | self.chain_query_expansion
            | self.document_manager.retriever
            | self.format_documents
        )

        system_template = f"{self.main_instruction}\n{{context}}"
        human_template = "{question}"
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", system_template),
                MessagesPlaceholder(variable_name="history"),
                ("human", human_template),
            ]
        )

        chain_answer = prompt_template | self.llm_main | StrOutputParser()

        return RunnableParallel(
            question=itemgetter("question"),
            history=itemgetter("history"),
            context=chain_context,
        ).assign(answer=chain_answer)

    def format_documents(self, docs):
        context = "\n\n".join(
            [
                f"Document {i}:\n\n'''\n{doc.page_content}\n'''"
                for i, doc in enumerate(docs, start=1)
            ]
        )
        return f"{self.config.templates['context']}\n{context}"

    def get_response(self, question, history):
        return self.chain_with_documents.invoke(
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
