from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict):
    """
    Represents the state flowing through the agentic RAG graph.
    """
    chat_id: int
    original_query: str
    rewritten_query: Optional[str]
    chat_history: str          # pre-formatted string for the LLM context
    intent: Optional[str]      # 'direct_answer' | 'document_qa'
    retrieved_documents: List[Dict[str, Any]]  # [{text, source, chunk_id, ...}]
    sources: List[Dict[str, Any]]              # deduplicated sources for citations
    final_answer: Optional[str]
    verification_passed: bool
    error: Optional[str]
