"""Filesystem helpers used by Coding Review Agent tools."""

from __future__ import annotations

from pathlib import Path

from aicodingagentbackend.exceptions import InvalidRepositoryError, MissingFileError
from aicodingagentbackend.utils.file_utils import (
    build_tree,
    iter_repository_paths,
)

SOURCE_FILE_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".py",
        ".js",
        ".jsx",
        ".mjs",
        ".cjs",
        ".ts",
        ".tsx",
        ".java",
        ".go",
        ".rs",
        ".cs",
        ".html",
        ".htm",
        ".css",
        ".scss",
        ".sass",
        ".json",
        ".yml",
        ".yaml",
        ".md",
        ".markdown",
        ".toml",
        ".xml",
        ".sql",
        ".sh",
    }
)


def ensure_repository_root(repository_path: Path) -> Path:
    """Validate that the repository path exists and is a directory."""
    root = repository_path.resolve()
    if not root.exists() or not root.is_dir():
        raise InvalidRepositoryError(f"Repository path does not exist: {repository_path}")
    return root


def resolve_repo_file(repository_path: Path, relative_path: str) -> Path:
    """
    Resolve a user-provided relative path safely inside the repository.

    Rejects absolute paths and path-traversal attempts.
    """
    root = ensure_repository_root(repository_path)
    raw = (relative_path or "").strip().replace("\\", "/")
    if not raw:
        raise MissingFileError("File path is required")
    if raw.startswith("/") or raw.startswith("~") or Path(raw).is_absolute():
        raise MissingFileError("Absolute paths are not allowed; use a repository-relative path")

    candidate = (root / raw).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise MissingFileError("Path escapes the repository root") from exc

    if not candidate.exists() or not candidate.is_file():
        raise MissingFileError(f"File not found in repository: {raw}")
    return candidate


def read_text_file(path: Path, *, max_chars: int | None = None) -> str:
    """Read a text file with UTF-8, optionally truncating large content."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise MissingFileError(f"Unable to read file '{path.name}': {exc}") from exc

    if max_chars is not None and len(content) > max_chars:
        omitted = len(content) - max_chars
        return (
            content[:max_chars]
            + f"\n\n...[truncated {omitted} characters; file continues beyond the tool limit]..."
        )
    return content


def repository_tree(repository_path: Path) -> list[str]:
    """Return the repository folder/file tree as POSIX-style paths."""
    root = ensure_repository_root(repository_path)
    files, folders = iter_repository_paths(root)
    return build_tree(root, files, folders)


def list_files_by_suffix(repository_path: Path, suffix: str) -> list[str]:
    """List repository-relative files matching a suffix (e.g. ``.py``)."""
    root = ensure_repository_root(repository_path)
    files, _folders = iter_repository_paths(root)
    normalized = suffix.lower() if suffix.startswith(".") else f".{suffix.lower()}"
    return sorted(
        path.as_posix()
        for path in files
        if path.suffix.lower() == normalized
    )


def is_searchable_file(path: Path) -> bool:
    """Return True if the file should be included in code search."""
    if path.suffix.lower() in SOURCE_FILE_EXTENSIONS:
        return True
    # Extensionless common config files
    return path.name.lower() in {"dockerfile", "makefile", "jenkinsfile", "procfile"}


def search_in_repository(
    repository_path: Path,
    keyword: str,
    *,
    max_matches: int = 50,
) -> list[dict[str, str | int]]:
    """
    Search source files for a keyword (case-insensitive).

    Returns dicts with ``path``, ``line_number``, and ``matching_text``.
    """
    root = ensure_repository_root(repository_path)
    query = (keyword or "").strip()
    if not query:
        return []

    query_lower = query.lower()
    matches: list[dict[str, str | int]] = []
    files, _folders = iter_repository_paths(root)

    for relative in files:
        if len(matches) >= max_matches:
            break
        if not is_searchable_file(relative):
            continue

        absolute = root / relative
        try:
            text = absolute.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for line_number, line in enumerate(text.splitlines(), start=1):
            if query_lower in line.lower():
                matches.append(
                    {
                        "path": relative.as_posix(),
                        "line_number": line_number,
                        "matching_text": line.strip(),
                    }
                )
                if len(matches) >= max_matches:
                    break

    return matches
