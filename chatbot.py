# fmt: off

from operator import itemgetter

import streamlit as st
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_openai import ChatOpenAI

from document_manager import DocumentManager

# fmt: on


class ChatbotPipeline:
    def __init__(self):
        self.config = st.session_state.config
        self.document_manager = DocumentManager(self.config.docs)
        self.initialize_chain()

    def initialize_chain(self):
        system_message = " ".join(
            [
                self.config.messages["system"],
                self.config.topic,
                self.config.language_style,
                self.config.dialogue_pace,
            ]
        )
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", f"{system_message}\n\n{{context}}"),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{question}"),
            ]
        )
        model = ChatOpenAI(model=self.config.params["model"])
        rag_chain_from_documents = (
            RunnablePassthrough.assign(
                context=lambda x: self.format_documents(x["context"])
            )
            | prompt_template
            | model
            | StrOutputParser()
        )
        self.chain = RunnableParallel(
            {
                "question": itemgetter("question"),
                "history": itemgetter("history"),
                "context": itemgetter("question")
                | self.document_manager.retriever,
            }
        ).assign(answer=rag_chain_from_documents)

    def format_documents(self, docs):
        context = "\n\n".join(
            [
                f'Document {i}:\n\n"""\n{doc.page_content}\n"""'
                for i, doc in enumerate(docs, start=1)
            ]
        )
        return f"Use the following documents to answer the query.\n\n{context}"

    def get_response(self, question, history):
        response = self.chain.invoke(
            {
                "question": question,
                "history": history.messages,
            }
        )
        return response


class ChatbotAgent:
    def __init__(self):
        self.config = st.session_state.config
        self.pipeline = ChatbotPipeline()
        self.initialize_chat_history()

    def initialize_chat_history(self):
        """Initialize chat history."""
        self.chat_history = StreamlitChatMessageHistory()
        if not self.chat_history.messages:
            self.chat_history.add_ai_message(self.config.messages["initial"])

    def display_messages(self):
        """Display messages from the chat history."""
        for message in self.chat_history.messages:
            st.chat_message(message.type).write(message.content)

    def handle_input(self):
        """Handle chat input from the user."""
        if query := st.chat_input():
            st.chat_message("human").write(query)
            response = self.pipeline.get_response(query, self.chat_history)
            st.chat_message("ai").write(response["answer"])

            self.display_file_citations(response["context"])

            self.chat_history.add_user_message(query)
            self.chat_history.add_ai_message(response["answer"])

    def display_file_citations(self, citations):
        """Display citations for the files used in the chatbot."""
        label = "The following texts were used to answer the query:"
        expander = st.expander(label)
        for citation in citations:
            content = citation.page_content.replace("#", "")
            content = "\n".join([f"> {line}" for line in content.split("\n")])
            expander.markdown(content)

    def run(self):
        """Run the chatbot."""
        self.display_messages()
        self.handle_input()
