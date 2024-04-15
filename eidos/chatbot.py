import json
from operator import itemgetter

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
from langchain_openai import ChatOpenAI

from eidos.document_manager import DocumentManager


class ChatbotPipeline:
    def __init__(self, configuration):
        self.config = configuration
        self.document_manager = DocumentManager(configuration)

        self.initialize_llms()
        self.initialize_templates()

        self.chain_rag_route = self.create_chain_rag_route()
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

    def create_chain_answer(self):
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_template.strip()),
                MessagesPlaceholder(variable_name="history"),
                ("human", self.answer_template.strip()),
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
            st.write("🔍 Exploring deeper implications of your belief...")
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

        st.write("📝 Writing my final thoughts...")
        response = self.chain_answer.invoke(
            {
                "user_message": user_message,
                "history": messages,
                "context": context,
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
