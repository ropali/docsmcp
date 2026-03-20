from models.documents import Document
from splitters.base import TextSplitter


class RecursiveCharacterSplitter(TextSplitter):
    def __init__(self, chunk_size: int = 512, overlap: int = 64):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(self, doc: Document) -> list[Document]:
        text = doc.content
        chunks = []
        start = 0
        idx = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]
            chunks.append(
                Document(
                    content=chunk_text, metadata={**doc.metadata, "chunk_index": idx}
                )
            )
            start += self.chunk_size - self.overlap
            idx += 1
        return chunks
