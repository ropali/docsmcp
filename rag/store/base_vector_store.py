from models.documents import Document
from typing import Protocol


class VectorStore(Protocol):
    def upsert(self, docs: list[Document], vectors: list[list[float]]) -> None: ...

    def search(self, query_vector: list[float], top_k: int = 5) -> list[Document]: ...
