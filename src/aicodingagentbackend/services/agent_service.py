"""Service that resolves local repositories and runs the Coding Review Agent."""

from __future__ import annotations

from pathlib import Path

from agents import Runner
from agents.exceptions import AgentsException, MaxTurnsExceeded, ModelBehaviorError
from openai import APIError, AuthenticationError, OpenAIError, RateLimitError

from aicodingagentbackend.agents.coding_agent import create_coding_review_agent
from aicodingagentbackend.agents.context import RepositoryContext
from aicodingagentbackend.core.config import Settings
from aicodingagentbackend.core.groq_config import create_groq_run_config, ensure_groq_configured
from aicodingagentbackend.exceptions import (
    GroqAPIError,
    InvalidRepositoryError,
)
from aicodingagentbackend.schemas.chat import ChatResponse
from aicodingagentbackend.services.rag.retrieval_service import RetrievalService
from aicodingagentbackend.services.repository_resolver import RepositoryResolver


class AgentService:
    """Run the Coding Review Agent with RAG context for a cloned repository."""

    def __init__(
        self,
        settings: Settings,
        resolver: RepositoryResolver,
        retrieval_service: RetrievalService,
    ) -> None:
        self._settings = settings
        self._resolver = resolver
        self._retrieval_service = retrieval_service

    def resolve_repository_path(self, repository_name: str) -> Path:
        """Locate a cloned repository under ``app/repositories``."""
        return self._resolver.resolve(repository_name)

    async def ask(self, repository_name: str, question: str) -> ChatResponse:
        """Retrieve relevant chunks, then run the Coding Review Agent."""
        cleaned_question = (question or "").strip()
        if not cleaned_question:
            raise InvalidRepositoryError("question is required")

        repo_path = self._resolver.resolve(repository_name)
        canonical = self._retrieval_service.ensure_indexed(repository_name)
        ensure_groq_configured(self._settings)

        retrieved = self._retrieval_service.retrieve(canonical, cleaned_question)

        retrieved_context = self._retrieval_service.format_chunks_for_prompt(retrieved)

        context = RepositoryContext(
            repository_name=canonical,
            repository_path=repo_path,
        )
        agent = create_coding_review_agent(self._settings)

        prompt = (
            f"Repository name: {canonical}\n"
            f"Local path: {repo_path.as_posix()}\n\n"
            f"User question:\n{cleaned_question}\n\n"
            "Retrieved relevant chunks (use these first; call retrieve_relevant_chunks "
            "again only if you need a different semantic search; call read_file only "
            "when a full file is necessary):\n\n"
            f"{retrieved_context}"
        )

        try:
            result = await Runner.run(
                starting_agent=agent,
                input=prompt,
                context=context,
                max_turns=self._settings.agent_max_turns,
                run_config=create_groq_run_config(self._settings),
            )
        except MaxTurnsExceeded as exc:
            raise GroqAPIError(
                "The Coding Review Agent exceeded the maximum number of turns "
                "while answering. Try a more specific question."
            ) from exc
        except ModelBehaviorError as exc:
            raise GroqAPIError(f"Agent model behavior error: {exc}") from exc
        except AuthenticationError as exc:
            raise GroqAPIError(
                "Groq authentication failed. Check GROQ_API_KEY."
            ) from exc
        except RateLimitError as exc:
            raise GroqAPIError("Groq rate limit exceeded. Please retry shortly.") from exc
        except APIError as exc:
            raise GroqAPIError(f"Groq API error: {exc}") from exc
        except OpenAIError as exc:
            raise GroqAPIError(f"Groq error: {exc}") from exc
        except AgentsException as exc:
            raise GroqAPIError(f"Agent run failed: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 - map unexpected SDK failures
            raise GroqAPIError(f"Unexpected agent failure: {exc}") from exc

        answer = (result.final_output or "").strip()
        if not answer:
            answer = (
                "The agent completed without producing a textual answer. "
                "Please try rephrasing the question."
            )

        return ChatResponse(
            repository_name=canonical,
            question=cleaned_question,
            answer=answer,
            model=self._settings.groq_model,
            agent=agent.name,
        )
