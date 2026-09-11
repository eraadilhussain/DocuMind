from typing import List, Dict, Any

def reciprocal_rank_fusion(
    vector_results: List[Dict[str, Any]], 
    keyword_results: List[Dict[str, Any]], 
    k: int = 60
) -> List[Dict[str, Any]]:
    """
    Fuses results from multiple retrieval methods using Reciprocal Rank Fusion (RRF).
    """
    fused_scores = {}
    doc_payloads = {}
    
    # Process vector results
    for rank, res in enumerate(vector_results):
        doc_id = res['payload'].get('chunk_id')
        if not doc_id:
            continue
            
        if doc_id not in fused_scores:
            fused_scores[doc_id] = 0.0
            doc_payloads[doc_id] = res['payload']
            
        fused_scores[doc_id] += 1.0 / (k + rank + 1)
        
    # Process keyword results
    for rank, res in enumerate(keyword_results):
        doc_id = res['payload'].get('chunk_id')
        if not doc_id:
            continue
            
        if doc_id not in fused_scores:
            fused_scores[doc_id] = 0.0
            doc_payloads[doc_id] = res['payload']
            
        fused_scores[doc_id] += 1.0 / (k + rank + 1)
        
    # Sort documents by their RRF score
    sorted_docs = sorted(fused_scores.items(), key=lambda item: item[1], reverse=True)
    
    final_results = []
    for doc_id, score in sorted_docs:
        final_results.append({
            "chunk_id": doc_id,
            "fusion_score": score,
            "payload": doc_payloads[doc_id]
        })
        
    return final_results
