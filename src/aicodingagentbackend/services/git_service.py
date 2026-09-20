"""Git operations for cloning and refreshing repositories."""

from __future__ import annotations

import os
import re
import shutil
import stat
import time
from pathlib import Path
from urllib.parse import urlparse

from git import GitCommandError, Repo

from aicodingagentbackend.core.config import Settings
from aicodingagentbackend.exceptions import (
    GitCloneError,
    InvalidGitHubURLError,
    PrivateRepositoryError,
    RepositoryNotFoundError,
)

_GITHUB_HOSTS = {"github.com", "www.github.com"}
_REPO_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


def _handle_rmtree_error(func: object, path: str, _exc: BaseException) -> None:
    """Clear the read-only flag (common under Windows .git) and retry removal."""
    try:
        os.chmod(path, stat.S_IWRITE)
        if callable(func):
            func(path)
    except OSError:
        pass


def _clear_readonly(path: Path) -> None:
    """Recursively clear the read-only bit so Windows can delete .git files."""
    for current_root, _dirs, files in os.walk(path):
        for name in files:
            file_path = os.path.join(current_root, name)
            try:
                os.chmod(file_path, stat.S_IWRITE)
            except OSError:
                continue


def remove_directory(path: Path, *, retries: int = 5) -> None:
    """
    Force-delete a directory tree.

    Git checkout files on Windows are often marked read-only; a plain
    ``shutil.rmtree`` fails without clearing those attributes first.
    """
    if not path.exists():
        return

    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            _clear_readonly(path)
            shutil.rmtree(path, onexc=_handle_rmtree_error)
            if not path.exists():
                return
        except OSError as exc:
            last_error = exc
            time.sleep(0.2 * (attempt + 1))

    raise GitCloneError(
        f"Failed to remove existing repository at '{path}': {last_error}"
    )


class GitService:
    """Clone and manage local copies of remote GitHub repositories."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def validate_github_url(self, url: str) -> tuple[str, str, str]:
        """
        Validate a GitHub repository URL.

        Returns:
            (normalized_clone_url, owner, repository_name)
        """
        raw = url.strip()
        if raw.endswith(".git"):
            raw = raw[:-4]

        parsed = urlparse(raw)
        if parsed.scheme not in {"http", "https"}:
            raise InvalidGitHubURLError(
                "GitHub URL must use http or https (e.g. https://github.com/user/project)"
            )

        host = (parsed.hostname or "").lower()
        if host not in _GITHUB_HOSTS:
            raise InvalidGitHubURLError("Only github.com repository URLs are supported")

        parts = [part for part in parsed.path.strip("/").split("/") if part]
        if len(parts) < 2:
            raise InvalidGitHubURLError(
                "GitHub URL must include owner and repository name"
            )

        owner, repo_name = parts[0], parts[1]
        if not _REPO_NAME_PATTERN.match(owner) or not _REPO_NAME_PATTERN.match(repo_name):
            raise InvalidGitHubURLError("Invalid GitHub owner or repository name")

        clone_url = f"https://github.com/{owner}/{repo_name}.git"
        return clone_url, owner, repo_name

    def local_path_for(self, owner: str, repo_name: str) -> Path:
        """Return the local directory path for a repository."""
        base = self._settings.ensure_repositories_dir()
        return base / owner / repo_name

    def clone_or_refresh(self, github_url: str) -> Path:
        """
        Clone a repository into the local repositories directory.

        If a previous clone exists, it is removed and replaced with a fresh clone.
        """
        clone_url, owner, repo_name = self.validate_github_url(github_url)
        destination = self.local_path_for(owner, repo_name)

        remove_directory(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)

        try:
            Repo.clone_from(
                clone_url,
                str(destination),
                multi_options=["--depth", "1"],
            )
        except GitCommandError as exc:
            remove_directory(destination)
            self._raise_mapped_clone_error(exc, owner, repo_name)
        except OSError as exc:
            remove_directory(destination)
            raise GitCloneError(f"Git clone failed: {exc}") from exc

        if not destination.exists():
            raise GitCloneError("Git clone failed: destination directory was not created")

        return destination

    def _raise_mapped_clone_error(
        self,
        exc: GitCommandError,
        owner: str,
        repo_name: str,
    ) -> None:
        stderr = (exc.stderr or "").lower() if isinstance(exc.stderr, str) else str(exc).lower()
        stdout = (exc.stdout or "").lower() if isinstance(exc.stdout, str) else ""
        combined = f"{stderr}\n{stdout}\n{str(exc).lower()}"

        if any(
            token in combined
            for token in (
                "not found",
                "repository not found",
                "does not exist",
                "could not read from remote",
            )
        ):
            if "authentication failed" in combined or "could not read username" in combined:
                raise PrivateRepositoryError(
                    f"Repository '{owner}/{repo_name}' appears to be private or requires authentication"
                ) from exc
            raise RepositoryNotFoundError(
                f"Repository '{owner}/{repo_name}' was not found on GitHub "
                "(it may also be private)"
            ) from exc

        if any(
            token in combined
            for token in (
                "authentication failed",
                "could not read username",
                "access denied",
                "permission denied",
                "403",
                "unauthorized",
            )
        ):
            raise PrivateRepositoryError(
                f"Repository '{owner}/{repo_name}' is private or access was denied"
            ) from exc

        raise GitCloneError(f"Git clone failed for '{owner}/{repo_name}': {exc}") from exc
