"""Semantic retrieval over indexed repository chunks."""

from __future__ import annotations

from aicodingagentbackend.core.config import Settings
from aicodingagentbackend.exceptions import InvalidRepositoryError, RepositoryNotIndexedError
from aicodingagentbackend.services.rag.chroma_service import ChromaService
from aicodingagentbackend.services.rag.embedding_service import EmbeddingService
from aicodingagentbackend.services.rag.models import RetrievedChunk
from aicodingagentbackend.services.repository_resolver import RepositoryResolver


class RetrievalService:
    """Retrieve the top semantic matches for a repository question."""

    def __init__(
        self,
        settings: Settings,
        resolver: RepositoryResolver,
        embedding_service: EmbeddingService,
        chroma_service: ChromaService,
    ) -> None:
        self._settings = settings
        self._resolver = resolver
        self._embedding_service = embedding_service
        self._chroma_service = chroma_service

    def ensure_indexed(self, repository_name: str) -> str:
        """
        Resolve the repository and ensure it has indexed chunks.

        Returns the canonical repository name.
        """
        repo_path = self._resolver.resolve(repository_name)
        canonical = self._resolver.canonical_name(repo_path)
        indexed = self._chroma_service.count_for_repository(canonical)
        if indexed == 0:
            raise RepositoryNotIndexedError(
                f"Repository '{canonical}' is not indexed. "
                "Run POST /repository/index first."
            )
        return canonical

    def retrieve(
        self,
        repository_name: str,
        question: str,
        *,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        """
        Embed the question and return top-k Chroma matches for the repository.

        Raises:
            RepositoryNotIndexedError: when the repository has zero indexed chunks.
        """
        cleaned = (question or "").strip()
        if not cleaned:
            raise InvalidRepositoryError("question is required")

        canonical = self.ensure_indexed(repository_name)

        query_embedding = self._embedding_service.embed_query(cleaned)
        limit = top_k if top_k is not None else self._settings.retrieval_top_k
        return self._chroma_service.query_repository(
            repository_name=canonical,
            query_embedding=query_embedding,
            top_k=limit,
        )

    def format_chunks_for_prompt(
        self,
        chunks: list[RetrievedChunk],
        *,
        max_chars: int | None = None,
    ) -> str:
        """Render retrieved chunks as agent/tool context text."""
        if not chunks:
            return "No relevant chunks were retrieved."

        budget = max_chars if max_chars is not None else self._settings.rag_context_max_chars
        sections: list[str] = []
        used_chars = 0
        for rank, chunk in enumerate(chunks, start=1):
            distance = (
                f"{chunk.distance:.4f}" if chunk.distance is not None else "n/a"
            )
            section = "\n".join(
                [
                    f"[Match {rank}] {chunk.file_path} "
                    f"(language={chunk.language}, chunk={chunk.chunk_number}, distance={distance})",
                    chunk.content,
                ]
            )
            separator_size = 10 if sections else 0
            remaining = budget - used_chars - separator_size
            if remaining <= 0:
                break
            if len(section) > remaining:
                section = section[:remaining].rsplit("\n", 1)[0].rstrip()
            sections.append(section)
            used_chars += separator_size + len(section)
            if len(section) < len(chunk.content):
                break
        return "\n\n-----\n\n".join(sections)
