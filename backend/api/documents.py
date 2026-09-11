from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
import uuid

from db.session import get_db
from models.chat import Chat
from models.document import Document, DocumentStatus, SourceType
from schemas.document import DocumentResponse
from api.chats import get_current_user
from models.user import User
from workers.document_worker import process_document
from rag.ingestion.indexer import QdrantIndexer

router = APIRouter()

default_upload_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", default_upload_dir)
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/chats/{chat_id}/documents", response_model=DocumentResponse)
async def upload_document(
    chat_id: int, 
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = file.filename.split(".")[-1].lower()
    if ext == "pdf":
        source_type = SourceType.PDF.value
    elif ext == "docx":
        source_type = SourceType.DOCX.value
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Only PDF and DOCX are allowed.")

    # Save file to disk
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    document = Document(
        chat_id=chat_id,
        file_name=file.filename,
        file_path=file_path,
        source_type=source_type,
        status=DocumentStatus.UPLOADED.value
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Trigger background worker to process the document (Extract -> Chunk -> Embed -> Index)
    background_tasks.add_task(process_document, document.id)

    return document

from pydantic import BaseModel, HttpUrl

class UrlInput(BaseModel):
    url: HttpUrl

@router.post("/chats/{chat_id}/urls", response_model=DocumentResponse)
async def add_url(
    chat_id: int, 
    url_in: UrlInput,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    document = Document(
        chat_id=chat_id,
        file_name=str(url_in.url),
        source_type=SourceType.URL.value,
        source_url=str(url_in.url),
        status=DocumentStatus.UPLOADED.value
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Trigger background worker to process the URL
    background_tasks.add_task(process_document, document.id)

    return document

@router.get("/chats/{chat_id}/documents", response_model=List[DocumentResponse])
def get_documents(chat_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    documents = db.query(Document).filter(Document.chat_id == chat_id).all()
    return documents

@router.delete("/chats/{chat_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    chat_id: int, 
    document_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    document = db.query(Document).filter(Document.id == document_id, Document.chat_id == chat_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    try:
        indexer = QdrantIndexer()
        indexer.delete_by_document(document_id)
    except Exception as e:
        # Proceed with DB deletion even if Qdrant fails (e.g., Qdrant is unreachable)
        print(f"Failed to delete document from Qdrant: {e}")
        
    db.delete(document)
    db.commit()
    
    return None
