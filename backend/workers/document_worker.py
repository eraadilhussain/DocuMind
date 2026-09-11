"""Real document processing pipeline.

Replaces the time.sleep placeholder with:
  UPLOADING → EXTRACTING → CHUNKING → EMBEDDING → INDEXING → READY | FAILED
"""
import os
from sqlalchemy.orm import Session

import db.base  # noqa: F401 — registers Chat/User/Message models so Document.chat relationship resolves
from models.document import Document, DocumentStatus, SourceType
from db.session import SessionLocal
from rag.ingestion.extractor import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_url,
)
from rag.ingestion.chunker import RecursiveTextChunker
from rag.ingestion.indexer import QdrantIndexer
from rag.embeddings.local_provider import LocalEmbeddingProvider

_embedding_provider: LocalEmbeddingProvider | None = None
_chunker: RecursiveTextChunker | None = None


def _get_embedding_provider() -> LocalEmbeddingProvider:
    global _embedding_provider
    if _embedding_provider is None:
        _embedding_provider = LocalEmbeddingProvider()
    return _embedding_provider


def _get_chunker() -> RecursiveTextChunker:
    global _chunker
    if _chunker is None:
        _chunker = RecursiveTextChunker(chunk_size=800, chunk_overlap=100)
    return _chunker


def _set_status(db: Session, document: Document, status: str, error: str = None):
    document.status = status
    if error:
        document.error_message = error
    db.commit()


def process_document(document_id: int):
    """Entry point called by FastAPI BackgroundTasks."""
    db = SessionLocal()
    document = None
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return

        _set_status(db, document, DocumentStatus.PROCESSING.value)

        # ── Step 1: Extract ────────────────────────────────────────────────
        _set_status(db, document, DocumentStatus.EXTRACTING.value)
        text = _extract_text(document)

        if not text.strip():
            raise ValueError("No text could be extracted from the document.")

        # ── Step 2: Chunk ──────────────────────────────────────────────────
        _set_status(db, document, DocumentStatus.CHUNKING.value)
        chunks = _get_chunker().create_chunks(
            text=text,
            document_id=document.id,
            chat_id=document.chat_id,
            source_name=document.file_name,
        )

        if not chunks:
            raise ValueError("Document produced no chunks after splitting.")

        # ── Step 3: Embed ──────────────────────────────────────────────────
        _set_status(db, document, DocumentStatus.EMBEDDING.value)
        provider = _get_embedding_provider()
        texts = [c["text"] for c in chunks]
        embeddings = provider.embed_documents(texts)

        # ── Step 4: Index ──────────────────────────────────────────────────
        _set_status(db, document, DocumentStatus.INDEXING.value)
        indexer = QdrantIndexer(dimension=provider.dimension)
        indexer.index_chunks(chunks, embeddings)

        # ── Done ───────────────────────────────────────────────────────────
        _set_status(db, document, DocumentStatus.READY.value)

    except Exception as e:
        if document:
            _set_status(db, document, DocumentStatus.FAILED.value, error=str(e))
    finally:
        db.close()


def _extract_text(document: Document) -> str:
    src = document.source_type

    if src == SourceType.URL.value:
        return extract_text_from_url(document.source_url)

    # File-based: document.file_path set by the upload endpoint
    file_path = document.file_path
    if not file_path or not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Uploaded file not found for document id={document.id} (path={file_path})"
        )

    if src == SourceType.PDF.value:
        return extract_text_from_pdf(file_path)
    elif src == SourceType.DOCX.value:
        return extract_text_from_docx(file_path)

    raise ValueError(f"Unsupported source_type: {src}")
