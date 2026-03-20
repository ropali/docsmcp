from sentence_transformers import SentenceTransformer
from embedding.base import Embedder


class LocalEmbedder(Embedder):
    """sentence-transformers for free local embeddings."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):

        self.model = SentenceTransformer(model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts).tolist()
