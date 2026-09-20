"""Repository analysis and indexing API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from aicodingagentbackend.core.dependencies import (
    get_ingestion_service,
    get_repository_service,
)
from aicodingagentbackend.schemas.repository import (
    AnalyzeRepositoryRequest,
    AnalyzeRepositoryResponse,
    IndexRepositoryRequest,
    IndexRepositoryResponse,
)
from aicodingagentbackend.services.rag.ingestion_service import IngestionService
from aicodingagentbackend.services.repository_service import RepositoryService

router = APIRouter(prefix="/repository", tags=["repository"])


@router.post(
    "/analyze",
    response_model=AnalyzeRepositoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze a GitHub repository",
    description=(
        "Clones a public GitHub repository locally and returns structural metadata: "
        "languages, framework, entry points, file tree, and related signals."
    ),
)
def analyze_repository(
    payload: AnalyzeRepositoryRequest,
    service: RepositoryService = Depends(get_repository_service),
) -> AnalyzeRepositoryResponse:
    return service.analyze(str(payload.github_url))


@router.post(
    "/index",
    response_model=IndexRepositoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Index a cloned repository into ChromaDB",
    description=(
        "Chunks supported source files, generates local Sentence Transformers "
        "embeddings, and stores "
        "them in the persistent ChromaDB collection for RAG retrieval."
    ),
)
def index_repository(
    payload: IndexRepositoryRequest,
    service: IngestionService = Depends(get_ingestion_service),
) -> IndexRepositoryResponse:
    return service.index_repository(payload.repository_name)
