"""
LangGraph agent nodes — all real LLM calls, no mocks.
"""
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient

from agent.state import AgentState
from agent.tools.query_rewriter import QueryRewriter
from rag.retrieval.hybrid import HybridRetriever
from rag.embeddings.local_provider import LocalEmbeddingProvider
from rag.reranking.local_reranker import LocalReranker
from llm.provider import get_llm
from core.config import settings

# ── Lazy singletons — created on first use, not at import time ────────────────
_query_rewriter: Optional[QueryRewriter] = None
_embedding_provider: Optional[LocalEmbeddingProvider] = None
_reranker: Optional[LocalReranker] = None
_qdrant_client: Optional[QdrantClient] = None


def _get_query_rewriter() -> QueryRewriter:
    global _query_rewriter
    if _query_rewriter is None:
        _query_rewriter = QueryRewriter()
    return _query_rewriter


def _get_embedding_provider() -> LocalEmbeddingProvider:
    global _embedding_provider
    if _embedding_provider is None:
        _embedding_provider = LocalEmbeddingProvider()
    return _embedding_provider


def _get_reranker() -> LocalReranker:
    global _reranker
    if _reranker is None:
        _reranker = LocalReranker()
    return _reranker


def _get_qdrant_client() -> QdrantClient:
    # Reuse the same singleton from the indexer so ingestion + retrieval
    # share the same in-memory store when Qdrant server is unavailable.
    from rag.ingestion.indexer import _get_client as _indexer_get_client
    return _indexer_get_client()

# ── Prompts ──────────────────────────────────────────────────────────────────

_INTENT_PROMPT = """You are a routing assistant. Classify the user's query into one of two categories:

- "document_qa": The query is asking for facts, specific entities, summaries, or ANY informational question. When in doubt, ALWAYS choose this.
- "direct_answer": The query is strictly a conversational greeting (e.g., "hi", "how are you") or a meta-question about your capabilities.

Respond with ONLY the category label — no explanation.

Query: {query}

Category:"""

_GENERATE_PROMPT = """You are DocuMind, an expert assistant that answers questions based on provided document excerpts.

Instructions:
- Answer ONLY using information found in the context below.
- If the context does not contain enough information, say so clearly.
- Be concise, precise, and cite the source when relevant.
- Use markdown formatting for readability.

Context:
{context}

Conversation history:
{chat_history}

User question: {query}

Answer:"""

_DIRECT_ANSWER_PROMPT = """You are DocuMind, a helpful AI assistant connected to a document retrieval system.

Instructions:
- Answer the user's question clearly and concisely using your general knowledge.
- If the user asks about your capabilities or whether you can read documents, confirm that you CAN read and retrieve information from the documents they upload.
- Use markdown formatting for readability.

Conversation history:
{chat_history}

User question: {query}

Answer:"""

_VERIFY_PROMPT = """You are a fact-checking assistant.

Given the ANSWER and the CONTEXT that was used to generate it, determine whether the answer is grounded in the context.

Respond with ONLY "YES" if the answer is supported by the context, or "NO" if it contains unsupported claims.

Context:
{context}

Answer:
{answer}

Grounded:"""


# ── Node implementations ─────────────────────────────────────────────────────

def rewrite_query_node(state: AgentState) -> AgentState:
    """Rewrites the query to be standalone based on chat history."""
    original_query = state["original_query"]
    chat_history = state.get("chat_history", "")

    try:
        rewritten_query = _get_query_rewriter().rewrite(original_query, chat_history)
    except Exception:
        rewritten_query = original_query  # graceful fallback

    return {"rewritten_query": rewritten_query}


def determine_intent_node(state: AgentState) -> AgentState:
    """Classifies the query as 'document_qa' or 'direct_answer' using an LLM."""
    query = state.get("rewritten_query") or state["original_query"]
    llm = get_llm(temperature=0.0)

    try:
        prompt = _INTENT_PROMPT.format(query=query)
        result = llm.invoke(prompt)
        label = result.content.strip().lower()
        intent = "document_qa" if "document" in label else "direct_answer"
    except Exception:
        intent = "document_qa"  # default to retrieval on failure

    return {"intent": intent}


def retrieve_documents_node(state: AgentState) -> AgentState:
    """Runs hybrid retrieval (vector + BM25 + RRF + rerank) for the query."""
    query = state.get("rewritten_query") or state["original_query"]
    chat_id = state["chat_id"]

    try:
        retriever = HybridRetriever(
            qdrant_client=_get_qdrant_client(),
            embedding_provider=_get_embedding_provider(),
            reranker=_get_reranker(),
        )
        docs = retriever.retrieve(query, chat_id, top_k=5)
    except Exception as e:
        docs = []

    # Deduplicate sources for citations
    seen_sources = set()
    sources = []
    for doc in docs:
        src = doc.get("source", "")
        if src and src not in seen_sources:
            seen_sources.add(src)
            sources.append({"source": src, "document_id": doc.get("document_id")})

    return {"retrieved_documents": docs, "sources": sources}


def generate_answer_node(state: AgentState) -> AgentState:
    """Generates a grounded answer using the retrieved documents."""
    query = state.get("rewritten_query") or state["original_query"]
    docs = state.get("retrieved_documents", [])
    chat_history = state.get("chat_history", "")
    intent = state.get("intent", "document_qa")

    llm = get_llm(temperature=0.3)

    if intent == "direct_answer":
        try:
            prompt = _DIRECT_ANSWER_PROMPT.format(
                chat_history=chat_history,
                query=query,
            )
            result = llm.invoke(prompt)
            final_answer = result.content.strip()
        except Exception as e:
            final_answer = f"I encountered an error while generating an answer: {e}"
        return {"final_answer": final_answer}

    # Build context block from retrieved chunks
    if docs:
        context_parts = []
        for i, doc in enumerate(docs, 1):
            src = doc.get("source", "document")
            context_parts.append(f"[{i}] (Source: {src})\n{doc.get('text', '')}")
        context = "\n\n---\n\n".join(context_parts)
    else:
        context = "No relevant document excerpts were found."

    try:
        prompt = _GENERATE_PROMPT.format(
            context=context,
            chat_history=chat_history,
            query=query,
        )
        result = llm.invoke(prompt)
        final_answer = result.content.strip()
    except Exception as e:
        final_answer = f"I encountered an error while generating an answer: {e}"

    return {"final_answer": final_answer}


def verify_answer_node(state: AgentState) -> AgentState:
    """LLM-based grounding check: is the answer supported by retrieved docs?"""
    docs = state.get("retrieved_documents", [])
    answer = state.get("final_answer", "")

    # If no documents were retrieved, skip verification
    if not docs:
        return {"verification_passed": True}

    context = "\n\n".join(doc.get("text", "") for doc in docs[:3])
    llm = get_llm(temperature=0.0)

    try:
        prompt = _VERIFY_PROMPT.format(context=context, answer=answer)
        result = llm.invoke(prompt)
        passed = "yes" in result.content.strip().lower()
    except Exception:
        passed = True  # pass through on error — don't block the user

    return {"verification_passed": passed}
