import json
from typing import List, Literal

import streamlit as st
from langchain_community.chat_message_histories.streamlit import (
    StreamlitChatMessageHistory,
)
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
)
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.tools import Tool
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


class WebSearchQueriesModel(BaseModel):
    """Model for generating web search queries."""

    queries: List[str] = Field(
        description="List of web search queries.",
        default=[],
    )


class BeliefAdvicesModel(BaseModel):
    """Model for advicing ways to explore beliefs further."""

    advices: List[str] = Field(
        description="List of advices for exploring beliefs further.",
        default=[],
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

        # fmt: off
        self.chain_belief_advices = (
            self.create_chain_with_structured_llm(
                "belief_advices",
                BeliefAdvicesModel,
            )
        )
        self.chain_web_queries = (
            self.create_chain_with_structured_llm(
                "web_search_queries",
                WebSearchQueriesModel,
            )
        )
        # fmt: on

        self.chain_question = self.create_chain_with_history("question")
        self.chain_answer = self.create_chain_with_history("answer")

    def initialize_llms(self):
        self.llm_main = ChatOpenAI(
            model=self.config.parameters["llm_main"],
            temperature=self.config.parameters["llm_temperature"],
        )
        self.llm_helper = ChatOpenAI(
            model=self.config.parameters["llm_helper"],
            temperature=self.config.parameters["llm_temperature"],
        )

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

    def create_chain_summary(self):
        prompt_template = ChatPromptTemplate.from_messages(
            [
                MessagesPlaceholder(variable_name="history"),
                ("human", self.config.templates["summary"]),
            ]
        )
        chain = prompt_template | self.llm_main | StrOutputParser()
        return chain.with_config({"run_name": "Dialogue Summary"})

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

    def create_chain_with_structured_llm(self, template_key, model):
        prompt_template = ChatPromptTemplate.from_messages(
            [
                MessagesPlaceholder(variable_name="history"),
                ("human", self.config.templates[template_key]),
            ]
        )
        llm = self.llm_main.with_structured_output(model)
        chain = prompt_template | llm
        run_name = f"{template_key.replace('_', ' ').title()} Generation"
        return chain.with_config({"run_name": run_name})

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

        st.write("🔗 Choosing best dialogue path...")
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

        st.write("❓ Generating best question to ask...")
        if "inconsistent" in quality:
            question_instruction = self.config.templates[
                "question_instruction_inconsistent"
            ]
        else:
            question_instruction = self.config.templates[
                "question_instruction_consistent"
            ]

        question = self.chain_question.invoke(
            {
                "user_message": user_message,
                "history": messages,
                "statement_quality": quality,
                "question_instruction": question_instruction,
            }
        )

        st.write("📝 Gathering my thoughts...")
        answer = self.chain_answer.invoke(
            {
                "user_message": user_message,
                "history": messages,
                "statement_quality": quality,
                "question": question,
            }
        )

        if context:
            context = context.split("\n\n", 1)[1]  # Remove the template

        return {"message": answer, "context": context}

    def get_summary(self, history):
        st.write("📄 Summarizing our conversation...")
        messages = self.get_messages_from_history(history)
        return self.chain_summary.invoke({"history": messages})

    def get_belief_advices(self, history, max_results=3):
        st.write("🧠 Exploring your beliefs further...")
        messages = self.get_messages_from_history(history)
        response = self.chain_belief_advices.invoke({"history": messages})
        return response.advices[:max_results]

    def format_reading_title(self, title):
        removables = [
            "(Stanford Encyclopedia of Philosophy)",
            "| Internet Encyclopedia of Philosophy",
        ]
        for removable in removables:
            title = title.replace(removable, "")
        return title.strip()

    def get_suggested_readings(self, history, max_results=5):
        st.write("🌐 Initializing web search tool...")
        search = GoogleSearchAPIWrapper()
        tool = Tool(
            name="Google Search Snippets",
            description="Search Google for recent results.",
            func=lambda query: search.results(query, 2),
        )

        st.write("❓ Generating relevant search queries...")
        messages = self.get_messages_from_history(history)
        response = self.chain_web_queries.invoke({"history": messages})

        st.write("🔍 Searching for online articles...")
        readings = []
        for query in response.queries:
            results = tool.run(query)
            for result in results:
                if not any(result["title"] == r["title"] for r in readings):
                    result["title"] = self.format_reading_title(result["title"])
                    readings.append(result)

        return readings[:max_results]


class ChatbotAgent:
    def __init__(self, configuration):
        self.config = configuration
        self.pipeline = ChatbotPipeline(configuration)
        self.chat_history = StreamlitChatMessageHistory()
        self.chat_count = 0

        self.add_initial_message()

    def add_initial_message(self):
        if self.chat_history.messages:
            return

        greeting = self.config.templates["greeting"]
        topic = self.config.selected_topic["title"]
        greeting = greeting.format(topic=topic)

        content = json.dumps({"message": greeting})
        self.chat_history.add_ai_message(content)

    def display_final_response(self, container):
        with container.status(
            "🔚 Wrapping up the conversation...",
            expanded=True,
        ) as status:
            summary = self.pipeline.get_summary(self.chat_history)
            advices = self.pipeline.get_belief_advices(self.chat_history)
            readings = self.pipeline.get_suggested_readings(self.chat_history)
            status.update(
                label="Conversation ended.",
                state="complete",
                expanded=False,
            )

        tab1, tab2, tab3 = container.tabs(
            [
                "📄 Summary",
                "🧠 Suggestions",
                "📚 Articles",
            ]
        )

        with tab1:
            st.markdown("### 📄 Dialogue Summary")
            st.markdown(summary)

        with tab2:
            st.markdown("### 🧠 Ways to Explore Beliefs Further")
            for advice in advices:
                with st.container(border=True):
                    st.markdown(advice)

        with tab3:
            st.markdown("### 📚 Interesting Online Articles")
            readings = [f"- [{r['title']}]({r['link']})" for r in readings]
            st.markdown("\n".join(readings))

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

        if self.chat_count >= self.config.parameters["max_k_chat"]:
            chat_container = st.chat_message("ai")
            self.display_final_response(chat_container)
            chat_container.warning("Conversation ended.", icon="⚠️")
            st.stop()

    def handle_input(self):
        if query := st.chat_input(key="chat_input"):
            st.chat_message("human").write(query)

            ai = st.chat_message("ai")
            with ai.status(
                "💭 Generating a meaningful response...",
                expanded=True,
            ):
                response = self.pipeline.get_response(query, self.chat_history)

            user_content = json.dumps({"message": query})
            self.chat_history.add_user_message(user_content)

            ai_content = json.dumps(response)
            self.chat_history.add_ai_message(ai_content)

            self.chat_count += 1
            st.rerun()

    def run(self):
        self.display_messages()
        self.handle_input()
