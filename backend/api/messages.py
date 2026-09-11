from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from db.session import get_db
from models.chat import Chat
from models.message import Message
from schemas.message import MessageCreate, MessageResponse
from api.chats import get_current_user
from models.user import User

router = APIRouter()

@router.get("/chats/{chat_id}/messages", response_model=List[MessageResponse])
def get_messages(chat_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    messages = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.created_at.asc()).all()
    return messages

@router.post("/chats/{chat_id}/messages", response_model=MessageResponse)
def create_message(chat_id: int, message_in: MessageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    message = Message(
        chat_id=chat_id,
        role=message_in.role,
        content=message_in.content
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
