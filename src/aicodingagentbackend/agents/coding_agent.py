"""Coding Review Agent built with the OpenAI Agents SDK (Groq backend)."""

from __future__ import annotations

from typing import Any

from agents import Agent, ModelSettings
from pydantic import BaseModel

from aicodingagentbackend.agents.context import RepositoryContext
from aicodingagentbackend.core.config import Settings
from aicodingagentbackend.core.groq_config import ensure_groq_compatible_tool_schemas
from aicodingagentbackend.tools.engineering_tools import (
    detect_bugs,
    generate_documentation,
    generate_tests,
    review_code,
    suggest_improvements,
)
from aicodingagentbackend.tools.repository_tools import (
    get_file_content,
    list_python_files,
    read_file,
    read_repository_structure,
    retrieve_relevant_chunks,
    search_code,
)

CODING_REVIEW_AGENT_NAME = "Coding Review Agent"

CODING_REVIEW_INSTRUCTIONS = """
You are an experienced Senior Software Engineer acting as an AI Software Engineer.

You analyze source code.
You review repositories.
You explain code.
You detect bugs.
You suggest improvements.
You generate tests and documentation.

Rules:
- Never invent code that is not present in the repository.
- Never modify repository files. Only analyze and generate response text.
- Only answer using repository content discovered via tools or retrieved RAG chunks.
- If information does not exist in the repository, say so clearly.
- Prefer semantic retrieval tools over reading the whole repository.
- For reviews, bugs, improvements, tests, and documentation:
  call the matching specialized tool first (review_code, detect_bugs,
  suggest_improvements, generate_tests, generate_documentation).
- Those specialized tools already use retrieve_relevant_chunks-style RAG search.
- Call retrieve_relevant_chunks() for ad-hoc questions or refined searches.
- Call read_file() / get_file_content() only when retrieved chunks are incomplete.
- Cite file paths (and line/chunk numbers when available).
- Be concrete and actionable.

Supported user intents:
- Review this repository / is this production ready?
- Find bugs
- Generate unit tests
- Improve this function / what should be refactored?
- Explain this class
- Write documentation
""".strip()

_REPO_TOOLS = [
    retrieve_relevant_chunks,
    review_code,
    detect_bugs,
    suggest_improvements,
    generate_tests,
    generate_documentation,
    read_repository_structure,
    list_python_files,
    read_file,
    search_code,
    get_file_content,
]


def create_coding_review_agent(
    settings: Settings,
    *,
    output_type: type[Any] | None = None,
    extra_instructions: str | None = None,
    include_tools: bool = True,
) -> Agent[RepositoryContext]:
    """Create the Coding Review Agent bound to RAG + engineering tools."""
    instructions = CODING_REVIEW_INSTRUCTIONS if include_tools else (
        "You are an experienced Senior Software Engineer. "
        "Analyze only the repository evidence included in the user message. "
        "Do not call tools. Return the requested structured result."
    )
    if extra_instructions:
        instructions = f"{instructions}\n\n{extra_instructions.strip()}"

    kwargs: dict[str, Any] = {
        "name": CODING_REVIEW_AGENT_NAME,
        "instructions": instructions,
        "model": settings.groq_model,
        "model_settings": ModelSettings(max_tokens=settings.agent_max_tokens),
        "tools": (
            ensure_groq_compatible_tool_schemas(list(_REPO_TOOLS))
            if include_tools
            else []
        ),
    }
    if output_type is not None:
        if not (isinstance(output_type, type) and issubclass(output_type, BaseModel)):
            raise TypeError("output_type must be a Pydantic BaseModel subclass")
        kwargs["output_type"] = output_type

    return Agent[RepositoryContext](**kwargs)
