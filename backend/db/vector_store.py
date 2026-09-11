from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from core.config import settings

def get_qdrant_client():
    client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
    return client

def init_qdrant_collection(client: QdrantClient, collection_name: str, dimension: int):
    # Create collection if it doesn't exist
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
        )
