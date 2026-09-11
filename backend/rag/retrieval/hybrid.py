from typing import List, Dict, Any

from qdrant_client import QdrantClient
from rag.retrieval.vector_search import VectorRetriever
from rag.retrieval.keyword_search import KeywordRetriever
from rag.retrieval.fusion import reciprocal_rank_fusion
from rag.reranking.local_reranker import LocalReranker
from rag.embeddings.base import BaseEmbeddingProvider
from rag.ingestion.indexer import QdrantIndexer, COLLECTION_NAME


class HybridRetriever:
    """
    Combines semantic vector search and BM25 keyword search via
    Reciprocal Rank Fusion (RRF), then optionally reranks the fused results.
    """

    def __init__(
        self,
        qdrant_client: QdrantClient,
        embedding_provider: BaseEmbeddingProvider,
        reranker: LocalReranker | None = None,
    ):
        self.vector_retriever = VectorRetriever(
            client=qdrant_client,
            collection_name=COLLECTION_NAME,
            embedding_provider=embedding_provider,
        )
        self.qdrant_client = qdrant_client
        self.embedding_provider = embedding_provider
        self.reranker = reranker or LocalReranker()

    def retrieve(
        self,
        query: str,
        chat_id: int,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Returns the top-k most relevant chunks for the query within the given chat.
        Each result is a dict: {text, source, chunk_id, fusion_score}
        """
        # 1. Vector search
        vector_results = self.vector_retriever.retrieve(query, chat_id, limit=top_k * 2)

        # 2. BM25 keyword search — scroll chunks from the shared client
        from rag.ingestion.indexer import COLLECTION_NAME as _COL
        from qdrant_client.models import Filter as _F, FieldCondition as _FC, MatchValue as _MV
        try:
            results, _ = self.qdrant_client.scroll(
                collection_name=_COL,
                scroll_filter=_F(must=[_FC(key="chat_id", match=_MV(value=chat_id))]),
                with_payload=True,
                with_vectors=False,
                limit=10_000,
            )
            all_chunks = [
                {"text": r.payload.get("text", ""), "metadata": r.payload}
                for r in results
            ]
        except Exception:
            all_chunks = []

        if all_chunks:
            keyword_retriever = KeywordRetriever(all_chunks)
            keyword_results = keyword_retriever.retrieve(query, limit=top_k * 2)
        else:
            keyword_results = []

        # 3. Reciprocal Rank Fusion
        fused = reciprocal_rank_fusion(vector_results, keyword_results, k=60)

        # 4. Rerank
        reranked = self.reranker.rerank(query, fused, top_k=top_k)

        # 5. Format for agent consumption
        formatted = []
        for doc in reranked:
            payload = doc.get("payload", {})
            formatted.append(
                {
                    "text": payload.get("text", ""),
                    "source": payload.get("source", "unknown"),
                    "chunk_id": payload.get("chunk_id", ""),
                    "document_id": payload.get("document_id"),
                    "fusion_score": doc.get("fusion_score", 0.0),
                }
            )

        return formatted
