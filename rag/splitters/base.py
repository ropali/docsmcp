from typing import Protocol
from rag.models.documents import Document


class TextSplitter(Protocol):
    def split(self, doc: Document) -> list[Document]: ...
