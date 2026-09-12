from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, Enum
from sqlalchemy.orm import relationship
import enum
from db.base_class import Base

class DocumentStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    EXTRACTING = "EXTRACTING"
    CHUNKING = "CHUNKING"
    EMBEDDING = "EMBEDDING"
    INDEXING = "INDEXING"
    READY = "READY"
    FAILED = "FAILED"

class SourceType(str, enum.Enum):
    PDF = "PDF"
    DOCX = "DOCX"
    URL = "URL"

class Document(Base):
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chat.id"), index=True, nullable=False)
    file_name = Column(String)
    file_path = Column(String, nullable=True)   # absolute path for file-based sources
    source_type = Column(String)  # Enum stored as string
    source_url = Column(String, nullable=True)
    status = Column(String, default=DocumentStatus.UPLOADED.value)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    chat = relationship("Chat", back_populates="documents")
