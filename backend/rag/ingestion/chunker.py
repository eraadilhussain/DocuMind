from typing import List, Dict, Any
import re


class RecursiveTextChunker:
    """
    Splits a long document text into overlapping chunks.

    Strategy (mirrors LangChain's RecursiveCharacterTextSplitter):
      1. Split by double newline (paragraph boundaries).
      2. If a segment is still too large, split by single newline.
      3. If still too large, split by sentence boundary (". ").
      4. Hard-split by character limit as a last resort.

    Overlap is achieved by carrying the last `chunk_overlap` characters
    of the previous chunk into the beginning of the next.
    """

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._separators = ["\n\n", "\n", ". ", " ", ""]

    def split_text(self, text: str) -> List[str]:
        """Returns a list of text chunks."""
        chunks: List[str] = []
        self._split_recursive(text, self._separators, chunks)
        return [c.strip() for c in chunks if c.strip()]

    def _split_recursive(self, text: str, separators: List[str], chunks: List[str]):
        if len(text) <= self.chunk_size:
            chunks.append(text)
            return

        sep = separators[0] if separators else ""
        remaining_seps = separators[1:] if separators else []

        if sep == "":
            # Hard character split
            for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
                chunks.append(text[i : i + self.chunk_size])
            return

        parts = text.split(sep)
        current = ""
        for part in parts:
            candidate = f"{current}{sep}{part}" if current else part
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    # Flush accumulated chunk
                    if len(current) > self.chunk_size:
                        self._split_recursive(current, remaining_seps, chunks)
                    else:
                        chunks.append(current)
                    # Start new chunk with overlap
                    overlap_text = current[-self.chunk_overlap:] if self.chunk_overlap else ""
                    current = f"{overlap_text}{sep}{part}" if overlap_text else part
                else:
                    # Single part is too big — recurse
                    self._split_recursive(part, remaining_seps, chunks)
                    current = ""

        if current:
            if len(current) > self.chunk_size:
                self._split_recursive(current, remaining_seps, chunks)
            else:
                chunks.append(current)

    def create_chunks(
        self, text: str, document_id: int, chat_id: int, source_name: str
    ) -> List[Dict[str, Any]]:
        """
        Splits text and returns structured chunk dicts ready for embedding + indexing.
        """
        raw_chunks = self.split_text(text)
        return [
            {
                "text": chunk,
                "metadata": {
                    "document_id": document_id,
                    "chat_id": chat_id,
                    "chunk_index": i,
                    "source": source_name,
                    "chunk_id": f"{document_id}_{i}",
                },
            }
            for i, chunk in enumerate(raw_chunks)
        ]
