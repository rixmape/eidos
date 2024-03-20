# fmt: off

from operator import itemgetter

import streamlit as st
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
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

        self.initialize_language_model()
        self.initialize_chatbot_instruction()
        self.initialize_chains()

    def initialize_language_model(self):
        self.language_model = ChatOpenAI(
            model=self.config.parameters["language_model"]
        )

    def initialize_chatbot_instruction(self):
        messages = [
            self.config.messages["system"],
            self.config.topic,
            self.config.language_style,
            self.config.dialogue_pace,
        ]

        if self.config.user_info:
            message = (
                "\n\nI am sharing some information about myself to improve"
                " our conversation. You must mention this into your responses:"
                f"\n\n'''\n{self.config.user_info}\n'''"
            )
            messages.append(message)

        self.system_message = " ".join(messages)

    def initialize_chains(self):
        self.chain_router = self.create_chain_router()
        self.chain_query_expansion = self.create_chain_query_expansion()
        self.chain_without_documents = self.create_chain_without_documents()
        self.chain_with_documents = self.create_chain_with_documents()
        self.complete_chain = self.create_complete_chain()

    def create_chain_router(self):
        template = (
            f"{self.config.messages['router']}"
            "\n\nQuestion:\n\n{question}"
            "\n\nNext Action:"
        )
        prompt_template = PromptTemplate.from_template(template)
        return prompt_template | self.language_model | StrOutputParser()

    def create_chain_query_expansion(self):
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", self.config.messages["query_expansion"]),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{question}"),
            ]
        )
        return prompt_template | self.language_model | StrOutputParser()

    def create_chain_without_documents(self):
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_message),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{question}"),
            ]
        )
        return prompt_template | self.language_model | StrOutputParser()

    def create_chain_with_documents(self):
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", f"{self.system_message}\n\n{{context}}"),
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
            | self.language_model
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
        self.initialize_chat_history()

    def set_style(self):
        style = """
        <style>
        div[data-testid="stChatMessage"] {
            gap: 1rem !important;
        }
        </style>
        """
        st.markdown(style, unsafe_allow_html=True)

    def initialize_chat_history(self):
        initial_message = "What's one thing in that you believe to be true?"
        if not self.chat_history.messages:
            self.chat_history.add_ai_message(initial_message)

    def display_messages(self):
        for message in self.chat_history.messages:
            st.chat_message(message.type).write(message.content)

    def handle_input(self):
        if query := st.chat_input():
            st.chat_message("human").write(query)
            answer = self.pipeline.get_response(query, self.chat_history)
            st.chat_message("ai").write(answer)

            self.chat_history.add_user_message(query)
            self.chat_history.add_ai_message(answer)

    def run(self):
        self.set_style()
        self.display_messages()
        self.handle_input()
