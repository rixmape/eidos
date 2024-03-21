# fmt: off

from operator import itemgetter

import streamlit as st
from langchain_community.chat_message_histories.streamlit import StreamlitChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI

from document_manager import DocumentManager

# fmt: on


class ChatbotPipeline:
    def __init__(self, configuration):
        self.config = configuration
        self.document_manager = DocumentManager(configuration)

        self.initialize_language_models()
        self.initialize_role_prompt()
        self.initialize_chains()

    def initialize_language_models(self):
        self.language_model_main = ChatOpenAI(
            model=self.config.parameters["language_model_main"],
        )
        self.language_model_helper = ChatOpenAI(
            model=self.config.parameters["language_model_helper"],
        )

    def initialize_role_prompt(self):
        messages = [
            self.config.templates["role"],
            self.config.selected_topic["instruction"],
            self.config.selected_language_style["instruction"],
            self.config.selected_dialogue_pace["instruction"],
        ]

        self.role_prompt = "\n".join(messages)

    def initialize_chains(self):
        self.chain_router = self.create_chain_router()
        self.chain_query_expansion = self.create_chain_query_expansion()
        self.chain_without_documents = self.create_chain_without_documents()
        self.chain_with_documents = self.create_chain_with_documents()
        self.complete_chain = self.create_complete_chain()

    def create_chain_router(self):
        template = self.config.templates["chain_router"]
        prompt_template = PromptTemplate.from_template(template)
        return prompt_template | self.language_model_helper | StrOutputParser()

    def create_chain_query_expansion(self):
        template = self.config.templates["query_expansion"]
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", template),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{question}"),
            ]
        )
        return prompt_template | self.language_model_helper | StrOutputParser()

    def create_chain_without_documents(self):
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", self.role_prompt),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{question}"),
            ]
        )
        return prompt_template | self.language_model_main | StrOutputParser()

    def create_chain_with_documents(self):
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", f"{self.role_prompt}\n\n{{context}}"),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{question}"),
            ]
        )
        context = (
            {
                "question": itemgetter("question"),
                "history": itemgetter("history"),
            }
            | self.chain_query_expansion
            | self.document_manager.retriever
            | self.format_documents
        )
        return (
            RunnablePassthrough.assign(context=context)
            | prompt_template
            | self.language_model_main
            | StrOutputParser()
        )

    def create_complete_chain(self):
        return {
            "action": self.chain_router,
            "question": itemgetter("question"),
            "history": itemgetter("history"),
        } | RunnableLambda(self.next_chain)

    def next_chain(self, input):
        return (
            self.chain_with_documents
            if "fetch" in input["action"]
            else self.chain_without_documents
        )

    def format_documents(self, docs):
        context = "\n\n".join(
            [
                f'Document {i}:\n\n"""\n{doc.page_content}\n"""'
                for i, doc in enumerate(docs, start=1)
            ]
        )
        return f"Use the following documents to answer the query.\n\n{context}"

    def get_response(self, question, history):
        return self.complete_chain.invoke(
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

        if not self.chat_history.messages:
            self.add_initial_message()

    def add_initial_message(self):
        template = self.config.templates["greeting"]
        claims = "\n".join(
            [f"- {claim}" for claim in self.config.selected_topic["claims"]]
        )
        initial_message = template.format(claims=claims)
        self.chat_history.add_ai_message(initial_message)

    def display_messages(self):
        for message in self.chat_history.messages:
            st.chat_message(message.type).markdown(message.content)

    def handle_input(self):
        if query := st.chat_input():
            st.chat_message("human").write(query)
            answer = self.pipeline.get_response(query, self.chat_history)
            st.chat_message("ai").write(answer)

            self.chat_history.add_user_message(query)
            self.chat_history.add_ai_message(answer)

    def run(self):
        self.display_messages()
        self.handle_input()
