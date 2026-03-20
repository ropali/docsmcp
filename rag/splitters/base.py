from typing import Protocol
from models.documents import Document


class TextSplitter(Protocol):
    def split(self, doc: Document) -> list[Document]: ...
