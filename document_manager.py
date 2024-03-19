import os

import chromadb
import streamlit as st
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders.text import TextLoader
from langchain_community.vectorstores.chroma import Chroma
from langchain_openai import OpenAIEmbeddings


class DocumentManager:
    def __init__(
        self,
        database_path="chromadb",
        allowed_file_types=["txt", "md"],
        documents_to_return_k=4,
        documents_to_fetch_k=50,
    ):
        self.database_path = database_path
        self.allowed_file_types = allowed_file_types
        self.documents_to_return_k = documents_to_return_k
        self.documents_to_fetch_k = documents_to_fetch_k

        self.config = st.session_state.config
        self.embedding_model = OpenAIEmbeddings(
            model=self.config.params["embedding_model"],
        )

        if os.path.exists(self.database_path):
            self.retriever = self.load_retriever()
        else:
            docs = self.read_documents()
            self.retriever = self.initialize_retriever(docs)

    def get_retriever(self, database):
        return database.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": self.documents_to_return_k,
                "fetch_k": self.documents_to_fetch_k,
            },
        )

    def load_retriever(self):
        client = chromadb.PersistentClient(path=self.database_path)
        vector_database = Chroma(
            embedding_function=self.embedding_model,
            client=client,
        )
        return self.get_retriever(vector_database)

    def read_documents(self, path="documents", limit=None):
        docs = []
        for filename in os.listdir(path)[:limit]:
            if filename.split(".")[-1] not in self.allowed_file_types:
                continue
            doc_loader = TextLoader(
                os.path.join(path, filename),
                encoding="utf-8",
            )
            docs.extend(doc_loader.load())
        return docs

    def initialize_retriever(self, docs):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=200,
        )

        documents = text_splitter.split_documents(docs)
        vector_database = Chroma.from_documents(
            documents,
            self.embedding_model,
            persist_directory=self.database_path,
        )
        vector_database.persist()
        return self.get_retriever(vector_database)
