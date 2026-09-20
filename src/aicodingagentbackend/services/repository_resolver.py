"""Shared local repository path resolution."""

from __future__ import annotations

import re
from pathlib import Path

from aicodingagentbackend.core.config import Settings
from aicodingagentbackend.exceptions import InvalidRepositoryError, RepositoryNotFoundError

_REPO_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
_OWNER_REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class RepositoryResolver:
    """Locate cloned repositories under the configured repositories directory."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def resolve(self, repository_name: str) -> Path:
        """
        Locate a cloned repository.

        Accepts either ``repo`` or ``owner/repo``.
        """
        name = (repository_name or "").strip().replace("\\", "/").strip("/")
        if not name:
            raise InvalidRepositoryError("repository_name is required")

        base = self._settings.ensure_repositories_dir()

        if "/" in name:
            if not _OWNER_REPO_PATTERN.match(name):
                raise InvalidRepositoryError(
                    "Invalid repository_name. Use 'repo' or 'owner/repo'."
                )
            candidate = (base / name).resolve()
            try:
                candidate.relative_to(base.resolve())
            except ValueError as exc:
                raise InvalidRepositoryError("Invalid repository path") from exc
            if not candidate.is_dir():
                raise RepositoryNotFoundError(
                    f"Repository '{name}' was not found locally. "
                    "Analyze it first via POST /repository/analyze."
                )
            return candidate

        if not _REPO_NAME_PATTERN.match(name):
            raise InvalidRepositoryError(
                "Invalid repository_name. Use letters, numbers, dots, underscores, or hyphens."
            )

        direct = base / name
        if direct.is_dir():
            return direct.resolve()

        matches: list[Path] = []
        if base.exists():
            for owner_dir in base.iterdir():
                if not owner_dir.is_dir():
                    continue
                candidate = owner_dir / name
                if candidate.is_dir():
                    matches.append(candidate.resolve())

        if not matches:
            raise RepositoryNotFoundError(
                f"Repository '{name}' was not found locally. "
                "Analyze it first via POST /repository/analyze."
            )
        if len(matches) > 1:
            options = ", ".join(
                f"{path.parent.name}/{path.name}" for path in sorted(matches)
            )
            raise InvalidRepositoryError(
                f"Multiple repositories named '{name}' were found ({options}). "
                "Pass repository_name as 'owner/repo'."
            )
        return matches[0]

    def canonical_name(self, repository_path: Path) -> str:
        """Return the repository folder name used for Chroma metadata."""
        return repository_path.name
