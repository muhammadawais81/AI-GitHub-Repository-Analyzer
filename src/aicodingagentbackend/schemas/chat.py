"""Pydantic schemas for Coding Review Agent chat."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request body for POST /chat."""

    repository_name: str = Field(
        ...,
        min_length=1,
        description="Local repository name (repo) or owner/repo",
        examples=["myproject", "octocat/Hello-World"],
    )
    question: str = Field(
        ...,
        min_length=1,
        description="Question about the cloned repository",
        examples=["Explain the authentication flow."],
    )


class ChatResponse(BaseModel):
    """Response body for POST /chat."""

    repository_name: str
    question: str
    answer: str
    model: str
    agent: str
