from eidos.configuration import Configuration
from eidos.document_manager import DocumentManager

if __name__ == "__main__":
    config = Configuration()
    doc_manager = DocumentManager(config)

    docs = doc_manager.get_documents()
    splits = doc_manager.split_documents(docs)

    for i, split in enumerate(splits, start=1):
        print(f"Upserting split {i} of {len(splits)}")
        id = doc_manager.vectorstore.add_documents([split])
