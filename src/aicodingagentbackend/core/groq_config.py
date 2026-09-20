"""Groq API configuration via the OpenAI-compatible client."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from agents import RunConfig
from agents.models.openai_provider import OpenAIProvider
from openai import APIError, AuthenticationError, OpenAIError, RateLimitError

from aicodingagentbackend.core.config import Settings
from aicodingagentbackend.exceptions import AgentConfigurationError, GroqAPIError

DEFAULT_GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def ensure_groq_configured(settings: Settings) -> None:
    """Validate that Groq credentials are present."""
    if not settings.groq_api_key:
        raise AgentConfigurationError(
            "GROQ_API_KEY is not configured. Set it in your .env file."
        )


@lru_cache
def _cached_groq_provider(api_key: str, base_url: str) -> OpenAIProvider:
    return OpenAIProvider(
        api_key=api_key,
        base_url=base_url,
        use_responses=False,
        buffer_streamed_tool_calls=True,
    )


def ensure_groq_compatible_tool_schemas(tools: list[Any]) -> list[Any]:
    """Ensure tool JSON schemas include non-empty ``properties`` (required by Groq)."""
    for tool in tools:
        schema = getattr(tool, "params_json_schema", None)
        if not isinstance(schema, dict):
            continue
        properties = schema.get("properties")
        if isinstance(properties, dict) and properties:
            continue
        # Groq rejects schemas where ``required`` exists but ``properties`` is missing/empty.
        schema["type"] = "object"
        schema["properties"] = {
            "_unused": {
                "type": "string",
                "description": "Unused compatibility field for Groq tool schemas.",
            }
        }
        if "required" not in schema or not isinstance(schema["required"], list):
            schema["required"] = []
        # Keep required empty so callers need not send `_unused`.
        schema["required"] = [name for name in schema["required"] if name in schema["properties"]]
    return tools


def create_groq_run_config(settings: Settings) -> RunConfig:
    """Build a RunConfig that routes the Agents SDK through Groq."""
    ensure_groq_configured(settings)
    provider = _cached_groq_provider(settings.groq_api_key, settings.groq_base_url)
    return RunConfig(
        model_provider=provider,
        tracing_disabled=True,
    )


def map_groq_exception(exc: Exception, *, action: str) -> GroqAPIError:
    """Convert OpenAI-compatible Groq client errors into domain errors."""
    if isinstance(exc, AuthenticationError):
        return GroqAPIError(
            "Groq authentication failed. Check GROQ_API_KEY."
        )
    if isinstance(exc, RateLimitError):
        return GroqAPIError(
            "Groq rate limit exceeded. Please retry shortly."
        )
    if isinstance(exc, APIError):
        status = getattr(exc, "status_code", None)
        if status == 400:
            return GroqAPIError(
                f"Groq rejected the request while {action}: {exc}"
            )
        if status == 404:
            return GroqAPIError(
                f"Groq model or endpoint not found while {action}. "
                "Verify GROQ_MODEL."
            )
        return GroqAPIError(f"Groq API error while {action}: {exc}")
    if isinstance(exc, OpenAIError):
        return GroqAPIError(f"Groq error while {action}: {exc}")
    return GroqAPIError(f"Unexpected Groq failure while {action}: {exc}")
