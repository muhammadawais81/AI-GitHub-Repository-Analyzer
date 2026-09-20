"""Pydantic schemas for repository analysis."""

from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl


class AnalyzeRepositoryRequest(BaseModel):
    """Request body for POST /repository/analyze."""

    github_url: HttpUrl = Field(
        ...,
        description="Public GitHub repository URL",
        examples=["https://github.com/user/project"],
    )


class LargestFile(BaseModel):
    """A file entry ranked by size."""

    path: str
    size_bytes: int


class AnalyzeRepositoryResponse(BaseModel):
    """Structured analysis result for a cloned repository."""

    repository_name: str
    framework: str | None = None
    languages: list[str]
    files: int
    folders: int
    readme: bool
    requirements: bool
    license: bool
    entry_file: str | None = None
    requirements_file: str | None = None
    python_version: str | None = None
    largest_files: list[LargestFile]
    folder_structure: list[str]
    tree: list[str]


class IndexRepositoryRequest(BaseModel):
    """Request body for POST /repository/index."""

    repository_name: str = Field(
        ...,
        min_length=1,
        description="Local repository name (repo) or owner/repo",
        examples=["portfolio", "octocat/Hello-World"],
    )


class IndexRepositoryResponse(BaseModel):
    """Response body for POST /repository/index."""

    status: str
    repository_name: str
    files_indexed: int
    chunks: int
