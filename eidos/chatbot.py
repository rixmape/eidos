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


class RouteModel(BaseModel):
    """Response model for routing a message to either LLM or vectorstore."""

    explanation: str = Field(
        description="Explanation for the route.",
        default="",
    )
    decision: Literal["llm", "vectorstore"] = Field(
        description="Name of the route.",
        default="llm",
    )


class StatementQualityModel(BaseModel):
    """Model for the logical quality of a statement."""

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

        self.chain_route = self.create_chain_route()
        self.chain_expansion = self.create_chain_expansion()
        self.chain_context = self.create_chain_context()
        self.chain_quality = self.create_chain_quality()
        self.chain_summary = self.create_chain_summary()

        self.chain_question = self.create_chain_with_history("question")
        self.chain_answer = self.create_chain_with_history("answer")

    def initialize_llms(self):
        self.llm_main = ChatOpenAI(model=self.config.parameters["llm_main"])
        self.llm_helper = ChatOpenAI(model=self.config.parameters["llm_helper"])

    def initialize_templates(self):
        instructions = [
            self.config.selected_topic["instruction"].strip(),
            self.config.selected_language_style["instruction"].strip(),
        ]

        template = self.config.templates["system"]
        template = template.format(instructions=" ".join(instructions))
        self.system_template = template.strip()

    def create_chain_route(self):
        template = self.config.templates["route"]
        prompt_template = PromptTemplate.from_template(template)
        llm = self.llm_helper.with_structured_output(RouteModel)
        chain = prompt_template | llm
        return chain.with_config({"run_name": "Dialogue Route"})

    def create_chain_expansion(self):
        template = self.config.templates["expansion"]
        prompt_template = PromptTemplate.from_template(template)
        chain = prompt_template | self.llm_helper | StrOutputParser()
        return chain.with_config({"run_name": "Text Expansion"})

    def create_chain_context(self):
        chain = (
            self.chain_expansion
            | self.document_manager.retriever
            | self.format_documents
        )
        return chain.with_config({"run_name": "Document Retrieval"})

    def create_chain_quality(self):
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", f"{self.system_template}\n\n{{context}}"),
                MessagesPlaceholder(variable_name="history"),
                ("human", self.config.templates["quality"]),
            ]
        )
        chain = (
            prompt_template
            | self.llm_main.with_structured_output(StatementQualityModel)
            | self.format_quality
        )
        return chain.with_config({"run_name": "Statement Quality"})

    def create_chain_with_history(self, template_key):
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_template),
                MessagesPlaceholder(variable_name="history"),
                ("human", self.config.templates[template_key]),
            ]
        )
        chain = prompt_template | self.llm_main | StrOutputParser()
        return chain.with_config(
            {
                "run_name": f"{template_key.capitalize()} Generation",
            }
        )

    def create_chain_summary(self):
        prompt_template = ChatPromptTemplate.from_messages(
            [
                MessagesPlaceholder(variable_name="history"),
                ("human", self.config.templates["summary"]),
            ]
        )
        return prompt_template | self.llm_helper | StrOutputParser()

    def format_documents(self, docs):
        context = "\n\n".join([f"'''\n{doc.page_content}\n'''" for doc in docs])
        return f"{self.config.templates['context']}\n\n{context}"

    def format_quality(self, quality):
        return (
            f"The statement is logically {quality.classification}."
            f" {quality.explanation}"
        )

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
        route = self.chain_route.invoke({"user_message": user_message})
        if route.decision == "vectorstore":
            st.write("📚 Reading philosophical texts...")
            context = self.chain_context.invoke({"user_message": user_message})
        else:
            context = None

        st.write("🔍 Checking for inconsistency...")
        quality = self.chain_quality.invoke(
            {
                "user_message": user_message,
                "history": messages,
                "context": context,
            }
        )

        st.write("❓ Generating the best question to ask...")
        if "inconsistent" in quality:
            question_instruction = self.config.templates[
                "question_instruction_inconsistent"
            ]
            answer_instruction = self.config.templates[
                "answer_instruction_inconsistent"
            ]
        else:
            question_instruction = self.config.templates[
                "question_instruction_consistent"
            ]
            answer_instruction = self.config.templates[
                "answer_instruction_consistent"
            ]

        question = self.chain_question.invoke(
            {
                "user_message": user_message,
                "history": messages,
                "statement_quality": quality,
                "question_instruction": question_instruction,
            }
        )

        st.write("📝 Bringing all my thoughts together...")
        answer_instruction = answer_instruction.format(question=question)
        answer = self.chain_answer.invoke(
            {
                "user_message": user_message,
                "history": messages,
                "statement_quality": quality,
                "question": question,
                "answer_instruction": answer_instruction,
            }
        )

        if context:
            context = context.split("\n\n", 1)[1]  # Remove the template

        return {"message": answer, "context": context}

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
