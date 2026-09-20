"""Shared context for Coding Review Agent tool calls."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class RepositoryContext:
    """Local context passed to tools for a single agent run."""

    repository_name: str
    repository_path: Path
