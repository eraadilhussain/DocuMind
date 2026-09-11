from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import (
    rewrite_query_node,
    determine_intent_node,
    retrieve_documents_node,
    generate_answer_node,
    verify_answer_node
)

def build_graph() -> StateGraph:
    """Builds and returns the compiled LangGraph for Agentic RAG."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("rewrite_query", rewrite_query_node)
    workflow.add_node("determine_intent", determine_intent_node)
    workflow.add_node("retrieve_documents", retrieve_documents_node)
    workflow.add_node("generate_answer", generate_answer_node)
    workflow.add_node("verify_answer", verify_answer_node)
    
    # Define edges
    workflow.set_entry_point("rewrite_query")
    workflow.add_edge("rewrite_query", "determine_intent")
    
    # Conditional edge based on intent
    def route_intent(state: AgentState):
        if state.get("intent") == "direct_answer":
            return "generate_answer"
        return "retrieve_documents"
        
    workflow.add_conditional_edges(
        "determine_intent",
        route_intent,
        {
            "retrieve_documents": "retrieve_documents",
            "generate_answer": "generate_answer"
        }
    )
    
    workflow.add_edge("retrieve_documents", "generate_answer")
    workflow.add_edge("generate_answer", "verify_answer")
    
    def route_verification(state: AgentState):
        if state.get("verification_passed"):
            return END
        # Here we could implement fallback logic like re-generating or querying again.
        # For now, end the process.
        return END

    workflow.add_conditional_edges(
        "verify_answer",
        route_verification,
        {
            END: END
        }
    )
    
    return workflow.compile()

# Global compiled graph
agent_graph = build_graph()
