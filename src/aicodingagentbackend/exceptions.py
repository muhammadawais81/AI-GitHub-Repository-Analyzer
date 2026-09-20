"""Domain exceptions for repository analysis, agent chat, and RAG."""

from __future__ import annotations


class RepositoryError(Exception):
    """Base exception for repository-related failures."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class InvalidGitHubURLError(RepositoryError):
    """Raised when the provided GitHub URL is malformed or unsupported."""

    def __init__(self, message: str = "Invalid GitHub URL") -> None:
        super().__init__(message, status_code=400)


class RepositoryNotFoundError(RepositoryError):
    """Raised when the remote or local repository does not exist."""

    def __init__(self, message: str = "Repository not found") -> None:
        super().__init__(message, status_code=404)


class PrivateRepositoryError(RepositoryError):
    """Raised when the repository is private or access is denied."""

    def __init__(self, message: str = "Private repository or access denied") -> None:
        super().__init__(message, status_code=403)


class GitCloneError(RepositoryError):
    """Raised when git clone fails for an unexpected reason."""

    def __init__(self, message: str = "Git clone failed") -> None:
        super().__init__(message, status_code=502)


class EmptyRepositoryError(RepositoryError):
    """Raised when the cloned repository contains no analyzable files."""

    def __init__(self, message: str = "Repository is empty") -> None:
        super().__init__(message, status_code=422)


class InvalidRepositoryError(RepositoryError):
    """Raised when a repository name or local path is invalid."""

    def __init__(self, message: str = "Invalid repository") -> None:
        super().__init__(message, status_code=400)


class MissingFileError(RepositoryError):
    """Raised when a requested repository file does not exist."""

    def __init__(self, message: str = "File not found in repository") -> None:
        super().__init__(message, status_code=404)


class GroqAPIError(RepositoryError):
    """Raised when the Groq API or Agents SDK call fails."""

    def __init__(self, message: str = "Groq API error") -> None:
        super().__init__(message, status_code=502)


class AgentConfigurationError(RepositoryError):
    """Raised when required agent configuration is missing."""

    def __init__(self, message: str = "Agent configuration error") -> None:
        super().__init__(message, status_code=500)


class RepositoryNotIndexedError(RepositoryError):
    """Raised when a repository has not been indexed into ChromaDB."""

    def __init__(self, message: str = "Repository is not indexed") -> None:
        super().__init__(message, status_code=404)


class EmbeddingError(RepositoryError):
    """Raised when embedding generation fails."""

    def __init__(self, message: str = "Embedding failure") -> None:
        super().__init__(message, status_code=502)


class ChromaDBError(RepositoryError):
    """Raised when ChromaDB is unavailable or operations fail."""

    def __init__(self, message: str = "ChromaDB unavailable") -> None:
        super().__init__(message, status_code=503)
