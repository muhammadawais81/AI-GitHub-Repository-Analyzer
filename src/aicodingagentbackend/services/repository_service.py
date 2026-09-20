"""Repository analysis orchestration service."""

from __future__ import annotations

from pathlib import Path

from aicodingagentbackend.core.config import Settings
from aicodingagentbackend.exceptions import EmptyRepositoryError
from aicodingagentbackend.schemas.repository import (
    AnalyzeRepositoryResponse,
    LargestFile,
)
from aicodingagentbackend.services.git_service import GitService
from aicodingagentbackend.utils import file_utils


class RepositoryService:
    """Clone a GitHub repository and produce a structured analysis report."""

    def __init__(self, settings: Settings, git_service: GitService) -> None:
        self._settings = settings
        self._git_service = git_service

    def analyze(self, github_url: str) -> AnalyzeRepositoryResponse:
        """Validate, clone, scan, and summarize a GitHub repository."""
        repo_path = self._git_service.clone_or_refresh(github_url)
        return self._analyze_local(repo_path)

    def _analyze_local(self, repo_path: Path) -> AnalyzeRepositoryResponse:
        files, folders = file_utils.iter_repository_paths(repo_path)

        if not files:
            raise EmptyRepositoryError(
                "Repository is empty or contains no analyzable files"
            )

        framework = file_utils.detect_framework(repo_path, files)
        requirements_file = file_utils.find_requirements_file(repo_path)
        largest = file_utils.largest_files(
            repo_path,
            files,
            limit=self._settings.largest_files_limit,
        )

        return AnalyzeRepositoryResponse(
            repository_name=repo_path.name,
            framework=framework,
            languages=file_utils.detect_languages(files),
            files=len(files),
            folders=len(folders),
            readme=file_utils.find_readme(repo_path, files),
            requirements=requirements_file is not None,
            license=file_utils.find_license(repo_path, files),
            entry_file=file_utils.detect_entry_file(repo_path, files, framework),
            requirements_file=requirements_file,
            python_version=file_utils.detect_python_version(repo_path),
            largest_files=[
                LargestFile(path=path, size_bytes=size) for path, size in largest
            ],
            folder_structure=file_utils.build_folder_structure(folders),
            tree=file_utils.build_tree(repo_path, files, folders),
        )
