"""Shared helpers for building RAG retrieval services inside tools."""

from __future__ import annotations

from aicodingagentbackend.core.config import Settings, get_settings
from aicodingagentbackend.services.rag.chroma_service import ChromaService
from aicodingagentbackend.services.rag.embedding_service import EmbeddingService
from aicodingagentbackend.services.rag.retrieval_service import RetrievalService
from aicodingagentbackend.services.repository_resolver import RepositoryResolver


def build_retrieval_service(settings: Settings | None = None) -> RetrievalService:
    """Construct a RetrievalService with default dependencies."""
    cfg = settings or get_settings()
    return RetrievalService(
        settings=cfg,
        resolver=RepositoryResolver(cfg),
        embedding_service=EmbeddingService(cfg),
        chroma_service=ChromaService(cfg),
    )


def retrieve_for_queries(
    repository_name: str,
    queries: list[str],
    *,
    top_k: int | None = None,
) -> str:
    """
    Run multiple semantic searches and merge unique chunks into one context block.

    Used by engineering analysis tools so they never load the whole repository.
    """
    settings = get_settings()
    service = build_retrieval_service(settings)
    canonical = service.ensure_indexed(repository_name)
    configured_limit = top_k if top_k is not None else settings.retrieval_top_k
    limit = min(configured_limit, settings.analysis_retrieval_top_k)

    seen: set[str] = set()
    sections: list[str] = []
    for query in queries:
        cleaned = query.strip()
        if not cleaned:
            continue
        chunks = service.retrieve(canonical, cleaned, top_k=limit)
        for chunk in chunks:
            key = f"{chunk.file_path}::{chunk.chunk_index}"
            if key in seen:
                continue
            seen.add(key)
            distance = f"{chunk.distance:.4f}" if chunk.distance is not None else "n/a"
            sections.append(
                "\n".join(
                    [
                        f"[query={cleaned!r}] {chunk.file_path} "
                        f"(language={chunk.language}, chunk={chunk.chunk_number}, distance={distance})",
                        chunk.content,
                    ]
                )
            )

    if not sections:
        return f"No relevant chunks found for repository '{canonical}'."
    context = (
        f"Repository: {canonical}\n"
        f"Retrieved {len(sections)} unique chunk(s) via semantic search.\n\n"
        + "\n\n-----\n\n".join(sections)
    )
    return context[: settings.rag_context_max_chars]
