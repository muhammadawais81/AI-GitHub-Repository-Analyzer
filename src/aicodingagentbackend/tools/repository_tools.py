"""OpenAI Agents SDK function tools for repository inspection and RAG retrieval."""

from __future__ import annotations

import json

from agents import RunContextWrapper, function_tool

from aicodingagentbackend.agents.context import RepositoryContext
from aicodingagentbackend.core.config import get_settings
from aicodingagentbackend.tools import repository_tools_impl as impl
from aicodingagentbackend.tools.rag_helpers import build_retrieval_service


@function_tool
def retrieve_relevant_chunks(
    ctx: RunContextWrapper[RepositoryContext],
    repository_name: str,
    question: str,
) -> str:
    """
    Semantically retrieve the top relevant code chunks for a question.

    Prefer this tool before reading whole files. Use repository_name of the
    active repository and a focused natural-language question.

    Args:
        repository_name: Local repository name (usually the active repo name).
        question: Natural-language question used for semantic search.
    """
    settings = get_settings()
    name = (repository_name or "").strip() or ctx.context.repository_name
    service = build_retrieval_service(settings)
    chunks = service.retrieve(
        name,
        question,
        top_k=settings.retrieval_top_k,
    )
    return service.format_chunks_for_prompt(chunks)


@function_tool
def read_repository_structure(
    ctx: RunContextWrapper[RepositoryContext],
    include_files: bool = True,
) -> str:
    """
    Return the folder/file tree of the currently selected repository.

    Args:
        include_files: When true (default), list files as well as folders.
    """
    tree = impl.repository_tree(ctx.context.repository_path)
    if not tree:
        return "Repository is empty (no files found outside ignored directories)."
    if not include_files:
        folders = [line for line in tree if line.endswith("/")]
        return "\n".join(folders) if folders else "\n".join(tree)
    return "\n".join(tree)


@function_tool
def list_python_files(
    ctx: RunContextWrapper[RepositoryContext],
    recursive: bool = True,
) -> str:
    """
    Return all Python (.py) files in the repository as a newline-separated list.

    Args:
        recursive: When true (default), include Python files in subfolders.
    """
    files = impl.list_files_by_suffix(ctx.context.repository_path, ".py")
    if not recursive:
        files = [path for path in files if "/" not in path and "\\" not in path]
    if not files:
        return "No Python files found in this repository."
    return "\n".join(files)


@function_tool
def read_file(ctx: RunContextWrapper[RepositoryContext], path: str) -> str:
    """
    Return the complete contents of a repository file.

    Use only when retrieved chunks are insufficient and you need the full file.

    Args:
        path: Repository-relative file path (for example: app/main.py).
    """
    settings = get_settings()
    absolute = impl.resolve_repo_file(ctx.context.repository_path, path)
    content = impl.read_text_file(absolute, max_chars=settings.agent_max_file_chars)
    return f"File: {path}\n\n{content}"


@function_tool
def search_code(ctx: RunContextWrapper[RepositoryContext], keyword: str) -> str:
    """
    Search every source file for a keyword and return matching lines.

    Args:
        keyword: Text to search for (case-insensitive).
    """
    settings = get_settings()
    matches = impl.search_in_repository(
        ctx.context.repository_path,
        keyword,
        max_matches=settings.agent_search_max_matches,
    )
    if not matches:
        return f"No matches found for keyword: {keyword!r}"

    lines = [
        f"{item['path']}:{item['line_number']}: {item['matching_text']}"
        for item in matches
    ]
    header = f"Found {len(matches)} match(es) for {keyword!r}:"
    return header + "\n" + "\n".join(lines)


@function_tool
def get_file_content(ctx: RunContextWrapper[RepositoryContext], path: str) -> str:
    """
    Return the selected file contents from the repository.

    Args:
        path: Repository-relative file path to read.
    """
    settings = get_settings()
    absolute = impl.resolve_repo_file(ctx.context.repository_path, path)
    payload = {
        "path": path.replace("\\", "/"),
        "size_bytes": absolute.stat().st_size,
        "content": impl.read_text_file(
            absolute,
            max_chars=settings.agent_max_file_chars,
        ),
    }
    return json.dumps(payload, ensure_ascii=False)
