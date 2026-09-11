from fastapi import APIRouter

api_router = APIRouter()

from api import chats, messages, documents, stream

api_router.include_router(chats.router, prefix="/chats", tags=["chats"])
api_router.include_router(messages.router, tags=["messages"])
api_router.include_router(documents.router, tags=["documents"])
api_router.include_router(stream.router, tags=["stream"])
