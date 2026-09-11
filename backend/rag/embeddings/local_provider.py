from typing import List

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings  # type: ignore

from .base import BaseEmbeddingProvider


class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """
    Uses the `all-MiniLM-L6-v2` sentence-transformer model for local embeddings.
    The model is downloaded automatically on first use (~90 MB).
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
        self._dimension = 384  # Dimension for all-MiniLM-L6-v2

    def embed_text(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        return self.embeddings.embed_documents(documents)

    @property
    def dimension(self) -> int:
        return self._dimension
