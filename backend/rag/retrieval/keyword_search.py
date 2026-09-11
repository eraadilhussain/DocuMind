from rank_bm25 import BM25Okapi
from typing import List, Dict, Any

class KeywordRetriever:
    def __init__(self, documents: List[Dict[str, Any]]):
        """
        Initializes the BM25 keyword retriever.
        :param documents: List of dicts, where each dict has a 'text' and 'metadata' key.
        """
        self.documents = documents
        self.tokenized_corpus = [self._tokenize(doc['text']) for doc in documents]
        
        if self.tokenized_corpus:
            self.bm25 = BM25Okapi(self.tokenized_corpus)
        else:
            self.bm25 = None

    def _tokenize(self, text: str) -> List[str]:
        # Basic tokenization, can be improved with stop words, stemming etc.
        return text.lower().split()

    def retrieve(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not self.bm25:
            return []
            
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top-k indices
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:limit]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0: # Only return matching documents
                results.append({
                    "score": scores[idx],
                    "payload": self.documents[idx]['metadata'],
                    "text": self.documents[idx]['text']
                })
        
        return results
