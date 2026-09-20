"""OpenAI Agents SDK tools for software-engineering analysis (Phase 4).

Each tool retrieves relevant repository chunks via RAG instead of loading
the entire repository, then returns analysis-oriented context for the agent.
"""

from __future__ import annotations

from agents import RunContextWrapper, function_tool

from aicodingagentbackend.agents.context import RepositoryContext
from aicodingagentbackend.tools.rag_helpers import retrieve_for_queries

_REVIEW_QUERIES = [
    "project architecture and entry points",
    "application structure modules packages",
    "error handling and configuration",
    "dependencies and main business logic",
    "code organization and maintainability",
]

_BUG_QUERIES = [
    "exception handling try except raise",
    "security authentication password secret token",
    "null none validation missing checks",
    "TODO FIXME bug hack workaround",
    "performance loops database query",
    "unused code dead code duplicate logic",
]

_IMPROVEMENT_QUERIES = [
    "complex functions long methods",
    "naming conventions classes functions",
    "architecture coupling dependency injection",
    "performance bottlenecks caching",
    "python best practices typing",
]

_TEST_QUERIES = [
    "public functions classes API endpoints",
    "validation input parsing",
    "authentication authorization",
    "business logic services",
    "existing tests pytest unittest",
]

_DOCS_QUERIES = [
    "README module overview",
    "public classes and functions",
    "API routes endpoints",
    "configuration settings",
    "main package entry points",
]


def _repo_name(ctx: RunContextWrapper[RepositoryContext], repository_name: str) -> str:
    return (repository_name or "").strip() or ctx.context.repository_name


@function_tool
def review_code(
    ctx: RunContextWrapper[RepositoryContext],
    repository_name: str,
    focus: str = "",
) -> str:
    """
    Retrieve code relevant to a professional repository review.

    Use this before producing overall score, strengths, weaknesses, and quality ratings.
    Does not modify any files.

    Args:
        repository_name: Local repository name (usually the active repo).
        focus: Optional area to emphasize (architecture, auth, APIs, etc.).
    """
    name = _repo_name(ctx, repository_name)
    queries = list(_REVIEW_QUERIES)
    if focus.strip():
        queries.insert(0, focus.strip())
    context = retrieve_for_queries(name, queries)
    return (
        "CODE REVIEW CONTEXT (RAG)\n"
        "Analyze only the retrieved chunks below. Produce: overall score (0-10), "
        "strengths, weaknesses, code quality, architecture quality, readability, "
        "and maintainability.\n\n"
        f"{context}"
    )


@function_tool
def detect_bugs(
    ctx: RunContextWrapper[RepositoryContext],
    repository_name: str,
    focus: str = "",
) -> str:
    """
    Retrieve code relevant to bug, security, and reliability analysis.

    Use this to find potential bugs, logic issues, dead code, duplicates,
    exception risks, security risks, and performance problems.
    Does not modify any files.

    Args:
        repository_name: Local repository name (usually the active repo).
        focus: Optional concern to emphasize.
    """
    name = _repo_name(ctx, repository_name)
    queries = list(_BUG_QUERIES)
    if focus.strip():
        queries.insert(0, focus.strip())
    context = retrieve_for_queries(name, queries)
    return (
        "BUG DETECTION CONTEXT (RAG)\n"
        "From the chunks below, list findings with severity, description, file, "
        "line when possible, and recommendation. Never invent files that are not shown.\n\n"
        f"{context}"
    )


@function_tool
def suggest_improvements(
    ctx: RunContextWrapper[RepositoryContext],
    repository_name: str,
    focus: str = "",
) -> str:
    """
    Retrieve code relevant to refactoring and improvement recommendations.

    Suggest better naming, simpler code, refactoring, performance improvements,
    cleaner architecture, and Python best practices. Does not modify any files.

    Args:
        repository_name: Local repository name (usually the active repo).
        focus: Optional area to improve.
    """
    name = _repo_name(ctx, repository_name)
    queries = list(_IMPROVEMENT_QUERIES)
    if focus.strip():
        queries.insert(0, focus.strip())
    context = retrieve_for_queries(name, queries)
    return (
        "IMPROVEMENT SUGGESTIONS CONTEXT (RAG)\n"
        "Recommend concrete improvements grounded only in the retrieved chunks.\n\n"
        f"{context}"
    )


@function_tool
def generate_tests(
    ctx: RunContextWrapper[RepositoryContext],
    repository_name: str,
    focus: str = "",
) -> str:
    """
    Retrieve code relevant to generating pytest unit tests.

    Cover normal cases, edge cases, invalid input, and missing test gaps.
    Return pytest code as text only — do not write files to disk.

    Args:
        repository_name: Local repository name (usually the active repo).
        focus: Optional module or feature to prioritize.
    """
    name = _repo_name(ctx, repository_name)
    queries = list(_TEST_QUERIES)
    if focus.strip():
        queries.insert(0, focus.strip())
    context = retrieve_for_queries(name, queries)
    return (
        "TEST GENERATION CONTEXT (RAG)\n"
        "Generate pytest tests for the behavior visible in these chunks. "
        "Include normal, edge, and invalid-input cases. Do not modify repository files.\n\n"
        f"{context}"
    )


@function_tool
def generate_documentation(
    ctx: RunContextWrapper[RepositoryContext],
    repository_name: str,
    focus: str = "",
) -> str:
    """
    Retrieve code relevant to generating professional documentation.

    Produce module summary, function/class descriptions, and README improvements.
    Do not modify repository files.

    Args:
        repository_name: Local repository name (usually the active repo).
        focus: Optional module or feature to document.
    """
    name = _repo_name(ctx, repository_name)
    queries = list(_DOCS_QUERIES)
    if focus.strip():
        queries.insert(0, focus.strip())
    context = retrieve_for_queries(name, queries)
    return (
        "DOCUMENTATION CONTEXT (RAG)\n"
        "Write documentation from the retrieved chunks only: module summary, "
        "function descriptions, class descriptions, and README improvements.\n\n"
        f"{context}"
    )
