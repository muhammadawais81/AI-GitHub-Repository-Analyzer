"""Repository indexing orchestration (chunk → embed → ChromaDB)."""

from __future__ import annotations

from aicodingagentbackend.core.config import Settings
from aicodingagentbackend.exceptions import EmptyRepositoryError
from aicodingagentbackend.schemas.repository import IndexRepositoryResponse
from aicodingagentbackend.services.rag.chunk_service import ChunkService
from aicodingagentbackend.services.rag.chroma_service import ChromaService
from aicodingagentbackend.services.rag.embedding_service import EmbeddingService
from aicodingagentbackend.services.repository_resolver import RepositoryResolver


class IngestionService:
    """Index a locally cloned repository into the RAG vector store."""

    def __init__(
        self,
        settings: Settings,
        resolver: RepositoryResolver,
        chunk_service: ChunkService,
        embedding_service: EmbeddingService,
        chroma_service: ChromaService,
    ) -> None:
        self._settings = settings
        self._resolver = resolver
        self._chunk_service = chunk_service
        self._embedding_service = embedding_service
        self._chroma_service = chroma_service

    def index_repository(self, repository_name: str) -> IndexRepositoryResponse:
        """Chunk, embed, and persist a repository; replaces any prior index."""
        repo_path = self._resolver.resolve(repository_name)
        canonical = self._resolver.canonical_name(repo_path)

        chunks = self._chunk_service.chunk_repository(repo_path, canonical)
        if not chunks:
            raise EmptyRepositoryError(
                f"Repository '{canonical}' has no supported files to index "
                "(.py, .js, .ts, .jsx, .tsx, .json, .yml, .yaml, .md)."
            )

        embeddings = self._embedding_service.embed_texts([chunk.content for chunk in chunks])
        self._chroma_service.delete_repository(canonical)
        stored = self._chroma_service.upsert_chunks(chunks, embeddings)

        files_indexed = len({chunk.file_path for chunk in chunks})
        return IndexRepositoryResponse(
            status="success",
            repository_name=canonical,
            files_indexed=files_indexed,
            chunks=stored,
        )
