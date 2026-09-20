"""Pydantic schemas for Phase 4 software-engineering analysis APIs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RepositoryAnalysisRequest(BaseModel):
    """Shared request body for analysis endpoints."""

    repository_name: str = Field(
        ...,
        min_length=1,
        description="Local repository name (repo) or owner/repo",
        examples=["portfolio", "pallets/flask"],
    )
    focus: str | None = Field(
        default=None,
        description="Optional focus area (module, feature, or concern)",
        examples=["authentication", "api routes"],
    )


class CodeReviewResponse(BaseModel):
    """Structured repository code review."""

    repository_name: str
    overall_score: float = Field(..., ge=0, le=10, description="Overall score from 0 to 10")
    strengths: list[str]
    weaknesses: list[str]
    code_quality: float = Field(..., ge=0, le=10)
    architecture_quality: float = Field(..., ge=0, le=10)
    readability: float = Field(..., ge=0, le=10)
    maintainability: float = Field(..., ge=0, le=10)
    summary: str


class BugFinding(BaseModel):
    """A single potential bug or risk finding."""

    severity: Literal["critical", "high", "medium", "low"]
    description: str
    file: str
    line: int | None = None
    recommendation: str


class BugsResponse(BaseModel):
    """Structured bug detection result."""

    repository_name: str
    bugs: list[BugFinding]
    count: int
    summary: str


class ImprovementSuggestion(BaseModel):
    """A single improvement recommendation."""

    category: str = Field(
        ...,
        description="e.g. naming, refactoring, performance, architecture, best_practices",
    )
    description: str
    file: str | None = None
    recommendation: str


class ImprovementsResponse(BaseModel):
    """Structured improvement suggestions."""

    repository_name: str
    improvements: list[ImprovementSuggestion]
    count: int
    summary: str


class GeneratedTestFile(BaseModel):
    """A generated pytest module."""

    module: str = Field(..., description="Suggested test module path, e.g. tests/test_auth.py")
    test_code: str
    covers: list[str] = Field(default_factory=list, description="Behaviors/cases covered")


class TestsResponse(BaseModel):
    """Structured generated pytest suite."""

    repository_name: str
    tests: list[GeneratedTestFile]
    missing_coverage: list[str] = Field(default_factory=list)
    notes: str


class FunctionDoc(BaseModel):
    """Documentation entry for a function."""

    name: str
    file: str
    description: str


class ClassDoc(BaseModel):
    """Documentation entry for a class."""

    name: str
    file: str
    description: str


class DocumentationResponse(BaseModel):
    """Structured generated documentation."""

    repository_name: str
    module_summary: str
    function_descriptions: list[FunctionDoc]
    class_descriptions: list[ClassDoc]
    readme_improvements: list[str]
    full_documentation: str
