from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from typing import List, Dict, Any
from rag.embeddings.base import BaseEmbeddingProvider


class VectorRetriever:
    def __init__(
        self,
        client: QdrantClient,
        collection_name: str,
        embedding_provider: BaseEmbeddingProvider,
    ):
        self.client = client
        self.collection_name = collection_name
        self.embedding_provider = embedding_provider

    def retrieve(self, query: str, chat_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        query_vector = self.embedding_provider.embed_text(query)

        # Filter by chat_id to ensure per-chat isolation
        search_filter = Filter(
            must=[
                FieldCondition(
                    key="chat_id",
                    match=MatchValue(value=chat_id),
                )
            ]
        )

        try:
            # Newer Qdrant client API
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=search_filter,
                limit=limit,
                with_payload=True,
            ).points
        except AttributeError:
            # Fallback for older client versions
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=limit,
                with_payload=True,
            )

        return [
            {"id": point.id, "score": point.score, "payload": point.payload}
            for point in results
        ]
