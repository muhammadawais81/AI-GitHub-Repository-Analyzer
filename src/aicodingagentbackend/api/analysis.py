"""Phase 4 software-engineering analysis API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from aicodingagentbackend.core.dependencies import get_analysis_service
from aicodingagentbackend.schemas.analysis import (
    BugsResponse,
    CodeReviewResponse,
    DocumentationResponse,
    ImprovementsResponse,
    RepositoryAnalysisRequest,
    TestsResponse,
)
from aicodingagentbackend.services.analysis_service import AnalysisService

router = APIRouter(tags=["analysis"])


@router.post(
    "/review",
    response_model=CodeReviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Review a repository",
    description=(
        "Runs a professional code review using RAG retrieval and the Coding Review Agent. "
        "Does not modify repository files."
    ),
)
async def review_repository(
    payload: RepositoryAnalysisRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> CodeReviewResponse:
    return await service.review(payload.repository_name, payload.focus)


@router.post(
    "/bugs",
    response_model=BugsResponse,
    status_code=status.HTTP_200_OK,
    summary="Detect potential bugs",
    description=(
        "Finds potential bugs, logic issues, security risks, and performance problems "
        "using RAG-backed analysis. Does not modify repository files."
    ),
)
async def detect_repository_bugs(
    payload: RepositoryAnalysisRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> BugsResponse:
    return await service.bugs(payload.repository_name, payload.focus)


@router.post(
    "/improvements",
    response_model=ImprovementsResponse,
    status_code=status.HTTP_200_OK,
    summary="Suggest improvements",
    description=(
        "Recommends naming, refactoring, performance, and architecture improvements. "
        "Does not modify repository files."
    ),
)
async def suggest_repository_improvements(
    payload: RepositoryAnalysisRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> ImprovementsResponse:
    return await service.improvements(payload.repository_name, payload.focus)


@router.post(
    "/tests",
    response_model=TestsResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate pytest tests",
    description=(
        "Generates pytest tests (as response text only) covering normal, edge, and "
        "invalid-input cases. Does not write files to the repository."
    ),
)
async def generate_repository_tests(
    payload: RepositoryAnalysisRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> TestsResponse:
    return await service.tests(payload.repository_name, payload.focus)


@router.post(
    "/documentation",
    response_model=DocumentationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate documentation",
    description=(
        "Generates module/function/class documentation and README improvement ideas. "
        "Does not modify repository files."
    ),
)
async def generate_repository_documentation(
    payload: RepositoryAnalysisRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> DocumentationResponse:
    return await service.documentation(payload.repository_name, payload.focus)
