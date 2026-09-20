"""FastAPI application entrypoint for the AI Coding Agent backend."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from aicodingagentbackend.api.analysis import router as analysis_router
from aicodingagentbackend.api.chat import router as chat_router
from aicodingagentbackend.api.repository import router as repository_router
from aicodingagentbackend.core.config import PROJECT_ROOT, get_settings
from aicodingagentbackend.exceptions import RepositoryError

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AI Coding Agent backend. "
        "Phase 1: repository cloning and structural analysis. "
        "Phase 2: Coding Review Agent (Agents SDK + Groq). "
        "Phase 3: RAG over ChromaDB with local Sentence Transformers embeddings. "
        "Phase 4: AI Software Engineer — review, bugs, tests, docs, improvements."
    ),
)

app.include_router(repository_router)
app.include_router(chat_router)
app.include_router(analysis_router)


@app.exception_handler(RepositoryError)
async def repository_error_handler(
    _request: Request,
    exc: RepositoryError,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Invalid request payload",
            "errors": exc.errors(),
        },
    )


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


def main() -> None:
    """Run the API with uvicorn (``python -m aicodingagentbackend.main``)."""
    import uvicorn

    uvicorn.run(
        "aicodingagentbackend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        reload_dirs=[str(PROJECT_ROOT / "src")] if settings.debug else None,
    )


if __name__ == "__main__":
    main()
