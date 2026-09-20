"""RAG data models shared across chunking, storage, and retrieval."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CodeChunk:
    """A single code/text chunk prepared for embedding and storage."""

    repository_name: str
    file_path: str
    chunk_index: int
    language: str
    content: str

    @property
    def chunk_number(self) -> int:
        """1-based chunk number for metadata/display."""
        return self.chunk_index + 1

    @property
    def document_id(self) -> str:
        """Stable Chroma document id."""
        safe_path = self.file_path.replace("\\", "/")
        return f"{self.repository_name}::{safe_path}::{self.chunk_index}"


@dataclass(frozen=True)
class RetrievedChunk:
    """A chunk returned from semantic retrieval."""

    repository_name: str
    file_path: str
    language: str
    chunk_index: int
    chunk_number: int
    content: str
    distance: float | None = None
