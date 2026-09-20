"""FastAPI dependency providers for shared services."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends

from aicodingagentbackend.core.config import Settings, get_settings
from aicodingagentbackend.services.agent_service import AgentService
from aicodingagentbackend.services.analysis_service import AnalysisService
from aicodingagentbackend.services.git_service import GitService
from aicodingagentbackend.services.rag.chunk_service import ChunkService
from aicodingagentbackend.services.rag.chroma_service import ChromaService, get_chroma_service
from aicodingagentbackend.services.rag.embedding_service import EmbeddingService
from aicodingagentbackend.services.rag.ingestion_service import IngestionService
from aicodingagentbackend.services.rag.retrieval_service import RetrievalService
from aicodingagentbackend.services.repository_resolver import RepositoryResolver
from aicodingagentbackend.services.repository_service import RepositoryService


def get_repository_resolver(
    settings: Settings = Depends(get_settings),
) -> RepositoryResolver:
    return RepositoryResolver(settings)


def get_git_service(settings: Settings = Depends(get_settings)) -> GitService:
    return GitService(settings)


def get_repository_service(
    settings: Settings = Depends(get_settings),
    git_service: GitService = Depends(get_git_service),
) -> RepositoryService:
    return RepositoryService(settings, git_service)


@lru_cache
def get_embedding_service_cached() -> EmbeddingService:
    return EmbeddingService(get_settings())


def get_embedding_service() -> EmbeddingService:
    return get_embedding_service_cached()


def get_chunk_service(settings: Settings = Depends(get_settings)) -> ChunkService:
    return ChunkService(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )


def get_retrieval_service(
    settings: Settings = Depends(get_settings),
    resolver: RepositoryResolver = Depends(get_repository_resolver),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    chroma_service: ChromaService = Depends(get_chroma_service),
) -> RetrievalService:
    return RetrievalService(settings, resolver, embedding_service, chroma_service)


def get_ingestion_service(
    settings: Settings = Depends(get_settings),
    resolver: RepositoryResolver = Depends(get_repository_resolver),
    chunk_service: ChunkService = Depends(get_chunk_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    chroma_service: ChromaService = Depends(get_chroma_service),
) -> IngestionService:
    return IngestionService(
        settings,
        resolver,
        chunk_service,
        embedding_service,
        chroma_service,
    )


def get_agent_service(
    settings: Settings = Depends(get_settings),
    resolver: RepositoryResolver = Depends(get_repository_resolver),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
) -> AgentService:
    return AgentService(settings, resolver, retrieval_service)


def get_analysis_service(
    settings: Settings = Depends(get_settings),
    resolver: RepositoryResolver = Depends(get_repository_resolver),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
) -> AnalysisService:
    return AnalysisService(settings, resolver, retrieval_service)
