from models.documents import Document
import chromadb


class ChromaVectoreStore:
    def __init__(self, collection_name: str):
        self.client = chromadb.PersistentClient(path="../../chroma.db")
        self.collection = self.client.get_or_create_collection(collection_name)

    def upsert(self, docs: list[Document], vectors: list[list[float]]) -> None:
        self.collection.upsert(
            ids=[f"{d.metadata['url']}::{d.metadata['chunk_index']}" for d in docs],
            embeddings=vectors,
            documents=[d.content for d in docs],
            metadatas=[d.metadata for d in docs],
        )

    def search(self, query_vector: list[float], top_k: int = 5) -> list[Document]:
        results = self.collection.query(
            query_embeddings=[query_vector], n_results=top_k
        )
        docs = []
        for content, meta in zip(results["documents"][0], results["metadatas"][0]):
            docs.append(Document(content=content, metadata=meta))
        return docs
