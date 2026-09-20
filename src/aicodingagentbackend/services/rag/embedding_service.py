"""Local Sentence Transformers embedding generation for RAG."""

from __future__ import annotations

from typing import Any

from aicodingagentbackend.core.config import Settings
from aicodingagentbackend.exceptions import EmbeddingError

_DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"

# Module-level singleton: load the SentenceTransformer model only once.
_model: Any | None = None
_model_name: str | None = None


def _get_sentence_transformer(model_name: str) -> Any:
    """Return a cached SentenceTransformer instance for ``model_name``."""
    global _model, _model_name

    if _model is not None and _model_name == model_name:
        return _model

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise EmbeddingError(
            "sentence-transformers is not installed. "
            "Run: pip install sentence-transformers torch"
        ) from exc

    try:
        _model = SentenceTransformer(model_name)
        _model_name = model_name
    except Exception as exc:  # noqa: BLE001
        raise EmbeddingError(
            f"Failed to load embedding model '{model_name}': {exc}"
        ) from exc

    return _model


class EmbeddingService:
    """Generate vector embeddings locally with Sentence Transformers."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def _model_name(self) -> str:
        return self._settings.embedding_model or _DEFAULT_MODEL

    def _encode(self, texts: list[str]) -> list[list[float]]:
        model = _get_sentence_transformer(self._model_name())
        batch_size = max(1, self._settings.embedding_batch_size)
        try:
            vectors = model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
        except Exception as exc:  # noqa: BLE001
            raise EmbeddingError(f"Embedding failure: {exc}") from exc

        result = [vector.tolist() for vector in vectors]
        if len(result) != len(texts):
            raise EmbeddingError(
                f"Embedding failure: expected {len(texts)} vectors, got {len(result)}"
            )
        return result

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts, batched according to settings."""
        if not texts:
            return []
        return self._encode(texts)

    def embed_query(self, question: str) -> list[float]:
        """Embed a single user question for retrieval."""
        cleaned = (question or "").strip()
        if not cleaned:
            raise EmbeddingError("Cannot embed an empty question")
        return self.embed_texts([cleaned])[0]
