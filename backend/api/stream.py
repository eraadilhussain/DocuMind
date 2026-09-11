"""
SSE Streaming Chat Endpoint.

POST /api/v1/chats/{chat_id}/stream
Body: {"message": "..."}

Yields Server-Sent Events:
  data: {"type": "token",   "content": "..."}
  data: {"type": "sources", "sources": [...]}
  data: {"type": "done"}
  data: {"type": "error",   "detail": "..."}
"""
import json
import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.session import get_db
from models.chat import Chat
from models.message import Message
from models.user import User
from services.context_manager import ContextManager
from agent.graph import agent_graph
from agent.state import AgentState
from api.chats import get_current_user

router = APIRouter()
_context_manager = ContextManager(max_recent_messages=10)


class StreamRequest(BaseModel):
    message: str


@router.post("/chats/{chat_id}/stream")
async def stream_chat(
    chat_id: int,
    body: StreamRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate chat ownership
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if not body.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Persist user message
    user_msg = Message(chat_id=chat_id, role="user", content=body.message)
    db.add(user_msg)
    db.commit()

    # Build chat history context
    recent_messages = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
        .limit(20)
        .all()
    )
    chat_history = _context_manager.build_context(
        chat_id=chat_id,
        recent_messages=recent_messages[:-1],  # exclude the message we just added
    )

    initial_state: AgentState = {
        "chat_id": chat_id,
        "original_query": body.message,
        "rewritten_query": None,
        "chat_history": chat_history,
        "intent": None,
        "retrieved_documents": [],
        "sources": [],
        "final_answer": None,
        "verification_passed": False,
        "error": None,
    }

    return StreamingResponse(
        _event_stream(initial_state, db, chat_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


async def _event_stream(
    state: AgentState, db: Session, chat_id: int
) -> AsyncGenerator[str, None]:
    """
    Runs the LangGraph agent synchronously in a thread pool
    and streams the final answer token-by-token via SSE.
    """
    full_answer = ""
    sources = []

    try:
        # Run the graph in a thread (it's sync) so we don't block the event loop
        final_state: AgentState = await asyncio.get_event_loop().run_in_executor(
            None, agent_graph.invoke, state
        )

        final_answer = final_state.get("final_answer") or "I could not generate an answer."
        sources = final_state.get("sources", [])

        # Stream the answer word-by-word for a nice typing effect
        words = final_answer.split(" ")
        for i, word in enumerate(words):
            token = word if i == 0 else f" {word}"
            full_answer += token
            event = json.dumps({"type": "token", "content": token})
            yield f"data: {event}\n\n"
            await asyncio.sleep(0.01)  # tiny delay for streaming feel

        # Send sources
        sources_event = json.dumps({"type": "sources", "sources": sources})
        yield f"data: {sources_event}\n\n"

    except Exception as e:
        error_event = json.dumps({"type": "error", "detail": str(e)})
        yield f"data: {error_event}\n\n"
        full_answer = f"An error occurred: {e}"

    finally:
        # Always persist the assistant message
        if full_answer.strip():
            assistant_msg = Message(
                chat_id=chat_id, role="assistant", content=full_answer
            )
            db.add(assistant_msg)

            # Check if chat needs a title
            chat = db.query(Chat).filter(Chat.id == chat_id).first()
            if chat and chat.title == "New Chat":
                from llm.provider import get_llm
                try:
                    llm = get_llm(temperature=0.7)
                    title_prompt = f"Summarize this user message into a concise chat title (max 5 words, no quotes):\n\n{state['original_query']}"
                    title_result = llm.invoke(title_prompt)
                    new_title = title_result.content.strip().strip('\"')
                    chat.title = new_title
                except Exception as e:
                    pass

            db.commit()

        # Signal stream end
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
