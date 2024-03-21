import os

import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders.text import TextLoader
from langchain_community.vectorstores.chroma import Chroma
from langchain_openai import OpenAIEmbeddings


class DocumentManager:
    def __init__(self, configuration):
        self.config = configuration
        self.initialize_embedding_model()

        if os.path.exists(self.config.parameters["database_path"]):
            self.retriever = self.load_retriever()
        else:
            self.documents = self.read_documents()
            self.retriever = self.initialize_retriever()

    def initialize_embedding_model(self):
        self.embedding_model = OpenAIEmbeddings(
            model=self.config.parameters["embedding_model"],
        )

    def get_retriever(self, database):
        return database.as_retriever(
            search_type=self.config.parameters["search_type"],
            search_kwargs={
                "k": self.config.parameters["docs_to_use"],
                "fetch_k": self.config.parameters["docs_to_process"],
            },
        )

    def load_retriever(self):
        client = chromadb.PersistentClient(
            path=self.config.parameters["database_path"]
        )
        vector_database = Chroma(
            embedding_function=self.embedding_model,
            client=client,
        )
        return self.get_retriever(vector_database)

    def read_documents(self, path="documents", limit=None):
        docs = []
        for filename in os.listdir(path)[:limit]:
            file_extension = filename.split(".")[-1]
            if file_extension not in self.config["allowed_file_types"]:
                continue
            doc_loader = TextLoader(
                os.path.join(path, filename),
                encoding="utf-8",
            )
            docs.extend(doc_loader.load())
        return docs

    def initialize_retriever(self):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=200,
        )
        splits = text_splitter.split_documents(self.documents)

        vector_database = Chroma.from_documents(
            splits,
            self.embedding_model,
            persist_directory=self.config.parameters["database_path"],
        )
        vector_database.persist()
        return self.get_retriever(vector_database)
