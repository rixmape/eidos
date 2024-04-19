import json
from operator import itemgetter
from typing import Literal

import streamlit as st
from langchain_community.chat_message_histories.streamlit import (
    StreamlitChatMessageHistory,
)
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
)
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI

from eidos.document_manager import DocumentManager


class InconsistencyModel(BaseModel):

    classification: Literal[
        "consistent",
        "inconsistent",
    ] = Field(
        description="Whether the statement is consistent or inconsistent.",
        default="consistent",
    )
    type: Literal[
        "fallacy",
        "external contradiction with philosophical texts",
        "external contradiction with previous statements",
        "internal contradiction within the statement",
        "unsupported claim",
    ] = Field(
        description="Type of inconsistency in the statement, if any.",
        default="",
    )
    explanation: str = Field(
        description="Explanation for the classification of the statement.",
        default="",
    )


class ChatbotPipeline:
    def __init__(self, configuration):
        self.config = configuration
        self.document_manager = DocumentManager(configuration)

        self.initialize_llms()
        self.initialize_templates()

        self.chain_rag_route = self.create_chain_rag_route()
        self.chain_query_expansion = self.create_chain_query_expansion()
        self.chain_context = self.create_chain_context()
        self.chain_inconsistency = self.create_chain_inconsistency()

        self.chain_question_consistent = self.create_chain_question_consistent()
        self.chain_answer_consistent = self.create_chain_answer_consistent()

        self.chain_question_inconsistent = (
            self.create_chain_question_inconsistent()
        )
        self.chain_answer_inconsistent = self.create_chain_answer_inconsistent()

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

    def create_chain_rag_route(self):
        template = self.config.templates["rag_route"]
        prompt_template = PromptTemplate.from_template(template)
        return prompt_template | self.llm_helper | StrOutputParser()

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

    def create_chain_inconsistency(self):
        human_template = self.config.templates["inconsistency"]
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_template.strip()),
                MessagesPlaceholder(variable_name="history"),
                ("human", human_template),
            ]
        )
        return prompt_template | self.llm_main.with_structured_output(
            InconsistencyModel
        )

    def create_chain_question_inconsistent(self):
        human_template = self.config.templates["question_inconsistent"]
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_template.strip()),
                MessagesPlaceholder(variable_name="history"),
                ("human", human_template),
            ]
        )
        return prompt_template | self.llm_main | StrOutputParser()

    def create_chain_question_consistent(self):
        human_template = self.config.templates["question_consistent"]
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_template.strip()),
                MessagesPlaceholder(variable_name="history"),
                ("human", human_template),
            ]
        )
        return prompt_template | self.llm_main | StrOutputParser()

    def create_chain_answer_consistent(self):
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_template.strip()),
                MessagesPlaceholder(variable_name="history"),
                ("human", self.config.templates["answer_consistent"]),
            ]
        )
        return prompt_template | self.llm_main | StrOutputParser()

    def create_chain_answer_inconsistent(self):
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_template.strip()),
                MessagesPlaceholder(variable_name="history"),
                ("human", self.config.templates["answer_inconsistent"]),
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

    def get_messages_from_history(self, history):
        messages = []
        for message in history.messages:
            content = json.loads(message.content)
            if message.type == "human":
                messages.append(HumanMessage(content["message"]))
            else:
                messages.append(AIMessage(content["message"]))
        return messages

    def get_response(self, user_message, history):
        messages = self.get_messages_from_history(history)

        st.write("🔗 Deciding whether to read philosophical texts...")
        rag_route = self.chain_rag_route.invoke(
            {
                "user_message": user_message,
                "history": messages,
            }
        )

        if "fetch" in rag_route:
            st.write("💡 Exploring deeper implications of your statement...")
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

            context = self.config.templates["context"].format(context=context)
        else:
            context = ""

        st.write("🔍 Checking for any inconsistencies...")
        quality = self.chain_inconsistency.invoke(
            {
                "user_message": user_message,
                "history": messages,
                "context": context,
            }
        )
        statement_quality_message = (
            f"The statement is logically {quality.classification}."
            f" {quality.explanation}"
        )

        st.write("❓ Generating the best question to ask...")
        question = self.chain_question_inconsistent.invoke(
            {
                "user_message": user_message,
                "history": messages,
                "context": "",  # TODO: Hack to avoid the context; fix it
                "statement_quality": statement_quality_message,
            }
        )

        st.write("📝 Bringing all my thoughts together...")
        response = self.chain_answer_inconsistent.invoke(
            {
                "user_message": user_message,
                "history": messages,
                "context": "",  # TODO: Hack to avoid the context; fix it
                "statement_quality": statement_quality_message,
                "question": question,
            }
        )

        if context:
            context = context.split("\n\n", 1)[1]  # Remove the template

        return {"message": response, "context": context}

    def get_summary(self, history):
        messages = self.get_messages_from_history(history)
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
        self.chat_count = 0

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
                        f"> {cleaned_context}"
                        for context in content["context"].split("\n")
                        if (cleaned_context := context.strip("'"))
                    ]
                    st.markdown("\n\n".join(contexts))

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
            self.chat_count += 1
            st.rerun()

    def display_summary(self):
        summary = self.pipeline.get_summary(self.chat_history)
        st.chat_message("ai").markdown(summary)

    def run(self):
        self.display_messages()

        if self.chat_count == 0:
            st.info("Share an idea about the topic.", icon="ℹ️")
        elif self.chat_count >= self.config.parameters["max_k_chat"]:
            self.display_summary()
            st.warning("You reached the limit.", icon="⚠️")
            return

        self.handle_input()
