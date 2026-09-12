import uuid
import logging
import os
from typing import List, Dict, Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    PayloadSchemaType
)
from core.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "documind_chunks"

_client: QdrantClient | None = None

def _get_client() -> QdrantClient:
    global _client
    if _client is not None:
        return _client

    try:
        remote = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
            timeout=10,
        )
        remote.get_collections()
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
    client = _get_client()
    existing = {c.name for c in client.get_collections().collections}
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
        )
    
    # Always attempt to create indexes (Qdrant ignores if they already exist)
    try:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="document_id",
            field_schema=PayloadSchemaType.INTEGER,
        )
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="chat_id",
            field_schema=PayloadSchemaType.INTEGER,
        )
    except Exception as e:
        logger.warning(f"Could not create payload index (might already exist): {e}")

class QdrantIndexer:
    def __init__(self, dimension: int = 384):
        self.client = _get_client()
        ensure_collection(dimension)

    def index_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]) -> None:
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
        self.client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
            ),
        )

    def scroll_chunks_for_chat(self, chat_id: int) -> List[Dict[str, Any]]:
        results, _ = self.client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=Filter(
                must=[FieldCondition(key="chat_id", match=MatchValue(value=chat_id))]
            ),
            with_payload=True,
            with_vectors=False,
            limit=10_000,
        )
        return [{"text": r.payload.get("text", ""), "metadata": r.payload} for r in results]
