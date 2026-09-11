from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from core.config import settings
from typing import List, Dict

class QueryRewriter:
    def __init__(self):
        # We can use a smaller/faster model for query rewriting if desired
        self.llm = ChatGroq(
            model=settings.LLM_MODEL, 
            api_key=settings.GROQ_API_KEY,
            temperature=0.0
        )
        self.prompt = PromptTemplate(
            input_variables=["chat_history", "current_query"],
            template="""You are a helpful assistant that rewrites a user's query to be a standalone query, 
based on the conversation history. If the query is already standalone, return it as is. 
Do not answer the query, just rewrite it.

Conversation History:
{chat_history}

Current Query: {current_query}

Standalone Query:"""
        )
        self.chain = self.prompt | self.llm

    def rewrite(self, current_query: str, chat_history: str) -> str:
        if not chat_history.strip():
            return current_query
            
        result = self.chain.invoke({
            "chat_history": chat_history,
            "current_query": current_query
        })
        return result.content.strip()
