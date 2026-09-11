from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from models.document import DocumentStatus, SourceType

class DocumentBase(BaseModel):
    file_name: Optional[str] = None
    source_type: str
    source_url: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: int
    chat_id: int
    status: DocumentStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
