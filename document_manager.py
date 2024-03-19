from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.chroma import Chroma
from langchain_openai import OpenAIEmbeddings


class DocumentManager:
    def __init__(self, docs):
        self.docs = docs
        self.retriever = self.initialize_retriever()

    def initialize_retriever(self):
        texts = []
        for doc in self.docs:
            text = str(doc.getvalue().decode("utf-8"))
            texts.append(text)

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=200,
        )

        documents = text_splitter.create_documents(texts)
        model = OpenAIEmbeddings()
        vector_database = Chroma.from_documents(documents, model)

        return vector_database.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 4, "fetch_k": 4},
        )
