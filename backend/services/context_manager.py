from typing import List, Dict, Any
from models.message import Message

class ContextManager:
    def __init__(self, max_recent_messages: int = 10):
        self.max_recent_messages = max_recent_messages

    def build_context(self, chat_id: int, recent_messages: List[Message], conversation_summary: str = "") -> str:
        """
        Builds the conversation context by combining recent messages and the overall summary.
        """
        context_parts = []
        
        if conversation_summary:
            context_parts.append(f"Summary of previous conversation:\n{conversation_summary}\n")
            
        if recent_messages:
            context_parts.append("Recent conversation history:")
            for msg in recent_messages[-self.max_recent_messages:]:
                role = "User" if msg.role == "user" else "Assistant"
                context_parts.append(f"{role}: {msg.content}")
                
        return "\n".join(context_parts)

    def format_for_llm(self, recent_messages: List[Message]) -> List[Dict[str, str]]:
        """
        Formats messages for LangChain or Groq API.
        """
        return [{"role": msg.role, "content": msg.content} for msg in recent_messages[-self.max_recent_messages:]]
