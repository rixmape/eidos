import json
from operator import itemgetter

import streamlit as st
from langchain_community.chat_message_histories.streamlit import (
    StreamlitChatMessageHistory,
)
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
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
        self.chain_summary = self.create_chain_summary()

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
        human_template = "{user_message}"
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", system_template),
                MessagesPlaceholder(variable_name="history"),
                ("human", human_template),
            ]
        )
        return prompt_template | self.llm_helper | StrOutputParser()

    def create_chain_context(self):
        chain_context = (
            {
                "user_message": itemgetter("user_message"),
                "history": itemgetter("history"),
            }
            | self.chain_query_expansion
            | self.document_manager.retriever
            | self.format_documents
        )

        return chain_context

    def create_chain_answer(self):
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_template),
                MessagesPlaceholder(variable_name="history"),
                ("human", self.answer_template),
            ]
        )
        return prompt_template | self.llm_main | StrOutputParser()

    def create_chain_summary(self):
        system_template = self.config.templates["summary"]
        prompt_template = ChatPromptTemplate.from_messages(
            [
                MessagesPlaceholder(variable_name="history"),
                ("human", system_template),
            ]
        )
        return prompt_template | self.llm_helper | StrOutputParser()

    def format_documents(self, docs):
        return "\n\n".join([f"'''\n{doc.page_content}\n'''" for doc in docs])

    def get_response(self, user_message, history):
        messages = []
        for message in history.messages:
            content = json.loads(message.content)
            if message.type == "human":
                messages.append(HumanMessage(content["message"]))
            else:
                messages.append(AIMessage(content["message"]))

        st.write("🔍 Exploring deeper implications...")
        expansion = self.chain_query_expansion.invoke(
            {
                "user_message": user_message,
                "history": messages,
            }
        )

        st.write("📚 Reading relevant philosophical texts...")
        context = self.chain_context.invoke(
            {
                "user_message": expansion,
                "history": messages,
            }
        )

        st.write("📝 Writing my final thoughts...")
        response = self.chain_answer.invoke(
            {
                "user_message": user_message,
                "history": messages,
                "context": context,
            }
        )

        return {"message": response, "context": context}

    def get_summary(self, history):
        return self.chain_summary.invoke(
            {
                "history": messages,
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
        topic = self.config.selected_topic["title"]
        greeting = greeting.format(topic=topic)

        content = json.dumps({"message": greeting})
        self.chat_history.add_ai_message(content)

    def display_messages(self):
        for message in self.chat_history.messages:
            chat = st.chat_message(message.type)
            content = json.loads(message.content)

            chat.write(content["message"])

            if message.type == "ai" and content.get("context"):
                with chat.expander("These texts helped me think better:"):
                    contexts = [
                        context
                        for context in content["context"].split("\n")
                        if context
                    ]
                    for context in contexts:
                        st.markdown(f"> {context.strip("'")}")

    def get_chat_messages(self):
        return [
            {"type": message.type, "content": message.content}
            for message in self.chat_history.messages
        ]

    def handle_input(self):
        if query := st.chat_input(key="chat_input"):
            st.chat_message("human").write(query)

            ai = st.chat_message("ai")
            with ai.status("🧠 Examining your statement..."):
                response = self.pipeline.get_response(query, self.chat_history)

            self.chat_history.add_user_message(json.dumps({"message": query}))
            self.chat_history.add_ai_message(json.dumps(response))
            self.prompt_count += 1
            st.rerun()

    def check_prompt_limit(self):
        return self.prompt_count >= self.config.parameters["max_prompt_count"]

    def display_summary(self):
        summary = self.pipeline.get_summary(self.chat_history)
        st.chat_message("ai").write(summary)

    def display_info_message(self):
        if len(self.chat_history.messages) == 1:
            st.info(self.config.tips["first_message"], icon="ℹ️")

    def run(self):
        self.display_messages()

        if self.check_prompt_limit():
            self.display_summary()

            message = "You reached the limit. Answer the survey form now."
            st.warning(message, icon="⚠️")

            return

        self.handle_input()
        self.display_info_message()
