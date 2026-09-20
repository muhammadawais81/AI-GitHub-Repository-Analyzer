"""Code chunking for RAG ingestion."""

from __future__ import annotations

from pathlib import Path

from aicodingagentbackend.services.rag.models import CodeChunk
from aicodingagentbackend.utils.file_utils import iter_repository_paths

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".json",
        ".yml",
        ".yaml",
        ".md",
    }
)

EXTENSION_LANGUAGE: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".json": "JSON",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".md": "Markdown",
}


class ChunkService:
    """Split supported source files into overlapping character chunks."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be non-negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def chunk_repository(self, repository_path: Path, repository_name: str) -> list[CodeChunk]:
        """Read supported files under ``repository_path`` and return chunks."""
        files, _folders = iter_repository_paths(repository_path)
        chunks: list[CodeChunk] = []

        for relative in files:
            suffix = relative.suffix.lower()
            if suffix not in SUPPORTED_EXTENSIONS:
                continue

            absolute = repository_path / relative
            try:
                text = absolute.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            if not text.strip():
                continue

            language = EXTENSION_LANGUAGE.get(suffix, "Unknown")
            file_path = relative.as_posix()
            for index, content in enumerate(self._split_text(text)):
                chunks.append(
                    CodeChunk(
                        repository_name=repository_name,
                        file_path=file_path,
                        chunk_index=index,
                        language=language,
                        content=content,
                    )
                )

        return chunks

    def _split_text(self, text: str) -> list[str]:
        """Split text into overlapping windows of ``chunk_size`` characters."""
        normalized = text.replace("\r\n", "\n")
        length = len(normalized)
        if length <= self._chunk_size:
            return [normalized]

        step = self._chunk_size - self._chunk_overlap
        parts: list[str] = []
        start = 0
        while start < length:
            end = min(start + self._chunk_size, length)
            parts.append(normalized[start:end])
            if end >= length:
                break
            start += step
        return parts
