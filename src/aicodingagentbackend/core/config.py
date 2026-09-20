"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Project root: .../aiCodingAgentBackend (three levels above this file)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_ROOT = Path(__file__).resolve().parents[1]


class Settings:
    """Runtime settings for the AI Coding Agent backend."""

    def __init__(self) -> None:
        self.app_name: str = os.getenv("APP_NAME", "AI Coding Agent Backend")
        self.app_version: str = os.getenv("APP_VERSION", "0.4.0")
        self.debug: bool = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"}
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "8000"))

        repos_dir = os.getenv("REPOSITORIES_DIR", "app/repositories")
        self.repositories_dir: Path = (
            Path(repos_dir) if Path(repos_dir).is_absolute() else PROJECT_ROOT / repos_dir
        )
        self.clone_timeout_seconds: int = int(os.getenv("CLONE_TIMEOUT_SECONDS", "120"))
        self.largest_files_limit: int = int(os.getenv("LARGEST_FILES_LIMIT", "10"))

        self.groq_api_key: str = os.getenv("GROQ_API_KEY", "").strip()
        self.groq_model: str = (
            os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
            or "llama-3.3-70b-versatile"
        )
        self.groq_base_url: str = (
            os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip()
            or "https://api.groq.com/openai/v1"
        )
        self.agent_max_turns: int = int(os.getenv("AGENT_MAX_TURNS", "25"))
        self.agent_max_file_chars: int = int(os.getenv("AGENT_MAX_FILE_CHARS", "120000"))
        self.agent_search_max_matches: int = int(os.getenv("AGENT_SEARCH_MAX_MATCHES", "50"))
        self.analysis_retrieval_top_k: int = int(
            os.getenv("ANALYSIS_RETRIEVAL_TOP_K", "2")
        )
        self.rag_context_max_chars: int = int(
            os.getenv("RAG_CONTEXT_MAX_CHARS", "8000")
        )
        self.agent_max_tokens: int = int(os.getenv("AGENT_MAX_TOKENS", "2000"))

        # Phase 3 — RAG
        chroma_dir = os.getenv("CHROMA_DIR", "")
        self.chroma_dir: Path = (
            Path(chroma_dir)
            if chroma_dir and Path(chroma_dir).is_absolute()
            else (PACKAGE_ROOT / "chroma_db" if not chroma_dir else PROJECT_ROOT / chroma_dir)
        )
        self.chroma_collection: str = os.getenv("CHROMA_COLLECTION", "repositories")
        self.embedding_model: str = (
            os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5").strip()
            or "BAAI/bge-small-en-v1.5"
        )
        self.chunk_size: int = int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "200"))
        self.retrieval_top_k: int = int(os.getenv("RETRIEVAL_TOP_K", "5"))
        self.embedding_batch_size: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "64"))

    def ensure_repositories_dir(self) -> Path:
        """Create the repositories directory if it does not exist."""
        self.repositories_dir.mkdir(parents=True, exist_ok=True)
        return self.repositories_dir

    def ensure_chroma_dir(self) -> Path:
        """Create the ChromaDB persistence directory if it does not exist."""
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        return self.chroma_dir


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (FastAPI-friendly DI)."""
    return Settings()
