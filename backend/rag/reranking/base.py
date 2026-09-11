from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseReranker(ABC):
    @abstractmethod
    def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Reranks a list of documents based on a query.
        
        :param query: The search query.
        :param documents: List of document dicts containing at least 'payload' and 'text'.
        :param top_k: Number of documents to return.
        :return: Reranked list of document dicts.
        """
        pass
