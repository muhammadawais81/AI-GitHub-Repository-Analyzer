"""Persistent ChromaDB storage for repository chunk embeddings."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from aicodingagentbackend.core.config import Settings, get_settings
from aicodingagentbackend.exceptions import ChromaDBError
from aicodingagentbackend.services.rag.models import CodeChunk, RetrievedChunk


class ChromaService:
    """Manage the persistent ``repositories`` Chroma collection."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: chromadb.PersistentClient | None = None
        self._collection: Collection | None = None

    def _get_client(self) -> chromadb.PersistentClient:
        if self._client is None:
            try:
                persist_dir = str(self._settings.ensure_chroma_dir())
                self._client = chromadb.PersistentClient(path=persist_dir)
            except Exception as exc:  # noqa: BLE001
                raise ChromaDBError(f"ChromaDB unavailable: {exc}") from exc
        return self._client

    def get_collection(self) -> Collection:
        """Return (or create) the repositories collection."""
        if self._collection is None:
            try:
                client = self._get_client()
                self._collection = client.get_or_create_collection(
                    name=self._settings.chroma_collection,
                    metadata={"hnsw:space": "cosine"},
                )
            except ChromaDBError:
                raise
            except Exception as exc:  # noqa: BLE001
                raise ChromaDBError(f"ChromaDB unavailable: {exc}") from exc
        return self._collection

    def delete_repository(self, repository_name: str) -> None:
        """Remove all chunks previously indexed for a repository."""
        collection = self.get_collection()
        try:
            existing = collection.get(where={"repository_name": repository_name})
            ids = existing.get("ids") or []
            if ids:
                collection.delete(ids=ids)
        except ChromaDBError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ChromaDBError(
                f"Failed to delete existing index for '{repository_name}': {exc}"
            ) from exc

    def upsert_chunks(
        self,
        chunks: list[CodeChunk],
        embeddings: list[list[float]],
    ) -> int:
        """Store chunk documents and embeddings. Returns number of upserted rows."""
        if len(chunks) != len(embeddings):
            raise ChromaDBError(
                f"Chunk/embedding length mismatch: {len(chunks)} vs {len(embeddings)}"
            )
        if not chunks:
            return 0

        collection = self.get_collection()
        ids = [chunk.document_id for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas: list[dict[str, Any]] = [
            {
                "repository_name": chunk.repository_name,
                "file_path": chunk.file_path,
                "language": chunk.language,
                "chunk_index": chunk.chunk_index,
                "chunk_number": chunk.chunk_number,
            }
            for chunk in chunks
        ]

        try:
            # Chroma accepts reasonably large batches; chunk further if needed.
            batch_size = 200
            for start in range(0, len(ids), batch_size):
                end = start + batch_size
                collection.upsert(
                    ids=ids[start:end],
                    documents=documents[start:end],
                    embeddings=embeddings[start:end],
                    metadatas=metadatas[start:end],
                )
        except Exception as exc:  # noqa: BLE001
            raise ChromaDBError(f"Failed to store embeddings in ChromaDB: {exc}") from exc

        return len(ids)

    def count_for_repository(self, repository_name: str) -> int:
        """Return how many chunks are indexed for a repository."""
        collection = self.get_collection()
        try:
            result = collection.get(where={"repository_name": repository_name})
            return len(result.get("ids") or [])
        except Exception as exc:  # noqa: BLE001
            raise ChromaDBError(
                f"Failed to query ChromaDB for '{repository_name}': {exc}"
            ) from exc

    def query_repository(
        self,
        repository_name: str,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        """Return the top-k semantic matches for a repository."""
        collection = self.get_collection()
        try:
            result = collection.query(
                query_embeddings=[query_embedding],
                n_results=max(1, top_k),
                where={"repository_name": repository_name},
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:  # noqa: BLE001
            raise ChromaDBError(f"ChromaDB query failed: {exc}") from exc

        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        retrieved: list[RetrievedChunk] = []
        for index, document in enumerate(documents):
            meta = metadatas[index] if index < len(metadatas) else {}
            distance = distances[index] if index < len(distances) else None
            chunk_index = int(meta.get("chunk_index", 0))
            chunk_number = int(meta.get("chunk_number", chunk_index + 1))
            retrieved.append(
                RetrievedChunk(
                    repository_name=str(meta.get("repository_name", repository_name)),
                    file_path=str(meta.get("file_path", "")),
                    language=str(meta.get("language", "Unknown")),
                    chunk_index=chunk_index,
                    chunk_number=chunk_number,
                    content=document or "",
                    distance=float(distance) if distance is not None else None,
                )
            )
        return retrieved


@lru_cache
def get_chroma_service() -> ChromaService:
    """Cached ChromaService for FastAPI dependency injection."""
    return ChromaService(get_settings())
