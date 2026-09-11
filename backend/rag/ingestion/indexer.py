"""
QdrantIndexer — handles collection management and chunk upserts.

Falls back to in-memory Qdrant automatically when the configured server
is unreachable (e.g. no Docker). In-memory mode persists only for the
lifetime of the process but lets the full pipeline run without Docker.
"""
import uuid
import logging
from typing import List, Dict, Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from core.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "documind_chunks"

# Module-level singleton so all workers share the same in-memory store
_client: QdrantClient | None = None


def _get_client() -> QdrantClient:
    global _client
    if _client is not None:
        return _client

    # Try the configured remote Qdrant first
    try:
        remote = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
            timeout=3,
        )
        remote.get_collections()          # probe — will throw if unreachable
        _client = remote
        logger.info("Connected to Qdrant at %s", settings.QDRANT_URL)
    except Exception as exc:
        logger.warning(
            "Qdrant server at %s unreachable (%s). "
            "Falling back to local file mode (./qdrant_data).",
            settings.QDRANT_URL,
            exc,
        )
        qdrant_path = os.getenv("QDRANT_PATH", "./qdrant_data")
        _client = QdrantClient(path=qdrant_path)

    return _client


def ensure_collection(dimension: int = 384) -> None:
    """Creates the Qdrant collection if it does not already exist."""
    client = _get_client()
    existing = {c.name for c in client.get_collections().collections}
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
        )


class QdrantIndexer:
    """Upserts document chunks (with their embeddings) into the Qdrant collection."""

    def __init__(self, dimension: int = 384):
        self.client = _get_client()
        ensure_collection(dimension)

    def index_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ) -> None:
        assert len(chunks) == len(embeddings), "chunks and embeddings must be the same length"

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={**chunk["metadata"], "text": chunk["text"]},
            )
            for chunk, vector in zip(chunks, embeddings)
        ]

        if points:
            self.client.upsert(collection_name=COLLECTION_NAME, points=points)

    def delete_by_document(self, document_id: int) -> None:
        """Removes all chunks belonging to a given document."""
        self.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            ),
        )

    def scroll_chunks_for_chat(self, chat_id: int) -> List[Dict[str, Any]]:
        """Returns all stored chunks for a chat — used by BM25 keyword retriever."""
        results, _ = self.client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="chat_id",
                        match=MatchValue(value=chat_id),
                    )
                ]
            ),
            with_payload=True,
            with_vectors=False,
            limit=10_000,
        )
        return [
            {"text": r.payload.get("text", ""), "metadata": r.payload}
            for r in results
        ]
