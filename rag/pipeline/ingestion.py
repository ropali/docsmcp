from dataclasses import dataclass
from store.base_vector_store import VectorStore
from embedding.base import Embedder
from splitters.base import TextSplitter
from loaders import DocumentLoader
from loguru import logger


@dataclass
class Page:
    html: str
    url: str
    title: str | None


class IngestionPipeline:
    def __init__(
        self,
        loader: DocumentLoader,
        splitter: TextSplitter,
        embedder: Embedder,
        store: VectorStore,
    ) -> None:
        self.loader = loader
        self.splitter = splitter
        self.embedder = embedder
        self.store = store

    def run(self, pages: list[Page]) -> None:
        logger.info("Running Ingestion Pipeline")
        all_chunks = []

        for page in pages:
            doc = self.loader.load(page.html, {"url": page.url, "title": page.title})

            chunks = self.splitter.split(doc)

            all_chunks.extend(chunks)

        # Batch embedding
        texts = [c.conten for c in all_chunks]

        vectors = self.embedder.embed(texts)
        self.store.upsert(all_chunks, vectors)

        logger.info(f"Ingested {len(all_chunks)} chunks from {len(pages)} pages")
