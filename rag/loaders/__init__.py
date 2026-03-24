from typing import Protocol

from bs4 import BeautifulSoup

from rag.models.documents import Document


class DocumentLoader(Protocol):
    def load(self, raw: str, metadata: dict) -> Document: ...


class HTMLLoader:
    def load(self, raw: str, metadata: dict) -> Document:
        soup = BeautifulSoup(raw, "html.parser")
        # Remove nav, footer, scripts — keep signal, drop noise
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return Document(content=text, metadata=metadata)
