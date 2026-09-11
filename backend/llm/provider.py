from langchain_groq import ChatGroq
from core.config import settings


def get_llm(temperature: float = 0.0, streaming: bool = False) -> ChatGroq:
    """
    Returns a configured ChatGroq LLM instance.
    Centralises model construction so nodes/workers don't import Groq directly.
    """
    return ChatGroq(
        model=settings.LLM_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=temperature,
        streaming=streaming,
    )
