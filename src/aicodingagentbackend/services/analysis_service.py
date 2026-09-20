"""Phase 4 analysis orchestration using the Coding Review Agent + RAG tools."""

from __future__ import annotations

import json
from typing import TypeVar

from agents import Runner
from agents.exceptions import AgentsException, MaxTurnsExceeded, ModelBehaviorError
from openai import APIError, AuthenticationError, OpenAIError, RateLimitError
from pydantic import BaseModel

from aicodingagentbackend.agents.coding_agent import create_coding_review_agent
from aicodingagentbackend.agents.context import RepositoryContext
from aicodingagentbackend.core.config import Settings
from aicodingagentbackend.core.groq_config import create_groq_run_config, ensure_groq_configured
from aicodingagentbackend.exceptions import GroqAPIError
from aicodingagentbackend.schemas.analysis import (
    BugsResponse,
    CodeReviewResponse,
    DocumentationResponse,
    ImprovementsResponse,
    TestsResponse,
)
from aicodingagentbackend.services.rag.retrieval_service import RetrievalService
from aicodingagentbackend.services.repository_resolver import RepositoryResolver

TModel = TypeVar("TModel", bound=BaseModel)


class AnalysisService:
    """Run structured software-engineering analyses against indexed repositories."""

    def __init__(
        self,
        settings: Settings,
        resolver: RepositoryResolver,
        retrieval_service: RetrievalService,
    ) -> None:
        self._settings = settings
        self._resolver = resolver
        self._retrieval_service = retrieval_service

    async def review(
        self,
        repository_name: str,
        focus: str | None = None,
    ) -> CodeReviewResponse:
        return await self._run_structured(
            repository_name=repository_name,
            focus=focus,
            output_type=CodeReviewResponse,
            tool_hint="review_code",
            task=(
                "Perform a professional code review of this repository. "
                "Call review_code first. Return overall_score, strengths, weaknesses, "
                "code_quality, architecture_quality, readability, maintainability, "
                "and a concise summary. Scores are 0-10."
            ),
        )

    async def bugs(
        self,
        repository_name: str,
        focus: str | None = None,
    ) -> BugsResponse:
        result = await self._run_structured(
            repository_name=repository_name,
            focus=focus,
            output_type=BugsResponse,
            tool_hint="detect_bugs",
            task=(
                "Detect potential bugs and risks. Call detect_bugs first. "
                "Include severity, description, file, line when possible, and recommendation. "
                "Set count to the number of bugs returned."
            ),
        )
        return result.model_copy(update={"count": len(result.bugs)})

    async def improvements(
        self,
        repository_name: str,
        focus: str | None = None,
    ) -> ImprovementsResponse:
        result = await self._run_structured(
            repository_name=repository_name,
            focus=focus,
            output_type=ImprovementsResponse,
            tool_hint="suggest_improvements",
            task=(
                "Suggest concrete improvements. Call suggest_improvements first. "
                "Cover naming, simplification, refactoring, performance, architecture, "
                "and Python best practices when evidence exists. "
                "Set count to the number of improvements returned."
            ),
        )
        return result.model_copy(update={"count": len(result.improvements)})

    async def tests(
        self,
        repository_name: str,
        focus: str | None = None,
    ) -> TestsResponse:
        return await self._run_structured(
            repository_name=repository_name,
            focus=focus,
            output_type=TestsResponse,
            tool_hint="generate_tests",
            task=(
                "Generate pytest unit tests as text only (do not write files). "
                "Call generate_tests first. Cover normal cases, edge cases, invalid input, "
                "and note missing coverage gaps."
            ),
        )

    async def documentation(
        self,
        repository_name: str,
        focus: str | None = None,
    ) -> DocumentationResponse:
        return await self._run_structured(
            repository_name=repository_name,
            focus=focus,
            output_type=DocumentationResponse,
            tool_hint="generate_documentation",
            task=(
                "Generate professional documentation. Call generate_documentation first. "
                "Include module_summary, function_descriptions, class_descriptions, "
                "readme_improvements, and full_documentation markdown."
            ),
        )

    async def _run_structured(
        self,
        *,
        repository_name: str,
        focus: str | None,
        output_type: type[TModel],
        tool_hint: str,
        task: str,
    ) -> TModel:
        cleaned_focus = (focus or "").strip()
        repo_path = self._resolver.resolve(repository_name)
        canonical = self._retrieval_service.ensure_indexed(repository_name)
        ensure_groq_configured(self._settings)

        seed_question = cleaned_focus or task
        seed_chunks = self._retrieval_service.retrieve(
            canonical,
            seed_question,
            top_k=min(
                self._settings.retrieval_top_k,
                self._settings.analysis_retrieval_top_k,
            ),
        )
        seed_context = self._retrieval_service.format_chunks_for_prompt(
            seed_chunks,
            max_chars=self._settings.rag_context_max_chars // 2,
        )
        schema_json = json.dumps(
            output_type.model_json_schema(),
            ensure_ascii=False,
            separators=(",", ":"),
        )

        agent = create_coding_review_agent(
            self._settings,
            include_tools=False,
            extra_instructions=(
                f"Use the retrieved evidence for the `{tool_hint}` analysis. "
                "Do not modify repository files. Return ONLY one valid JSON object "
                "that validates against this schema. Do not use markdown fences, "
                "comments, or an empty response.\n"
                f"JSON schema: {schema_json}"
            ),
        )

        prompt_parts = [
            f"Repository name: {canonical}",
            f"Local path: {repo_path.as_posix()}",
            "",
            f"Task:\n{task}",
        ]
        if cleaned_focus:
            prompt_parts.extend(["", f"Focus area:\n{cleaned_focus}"])
        prompt_parts.extend(
            [
                "",
                "Retrieved repository evidence:\n",
                seed_context,
            ]
        )
        prompt = "\n".join(prompt_parts)

        context = RepositoryContext(
            repository_name=canonical,
            repository_path=repo_path,
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
                "The analysis agent exceeded the maximum number of turns. "
                "Try a narrower focus."
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
        except Exception as exc:  # noqa: BLE001
            raise GroqAPIError(f"Unexpected analysis failure: {exc}") from exc

        output = result.final_output
        if isinstance(output, output_type):
            if hasattr(output, "repository_name"):
                return output.model_copy(update={"repository_name": canonical})
            return output

        if isinstance(output, str) and output.strip():
            try:
                parsed = output_type.model_validate_json(_extract_json_payload(output))
            except Exception as exc:  # noqa: BLE001
                raise GroqAPIError(
                    "Analysis completed but structured output could not be parsed."
                ) from exc
            if hasattr(parsed, "repository_name"):
                return parsed.model_copy(update={"repository_name": canonical})
            return parsed

        raise GroqAPIError(
            "Analysis completed without producing the expected structured response."
        )


def _extract_json_payload(text: str) -> str:
    """Return a JSON object string from model output (handles markdown fences)."""
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].lstrip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        payload = cleaned[start : end + 1]
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            return payload

        # Some Groq generations imitate a function call even when tools are off.
        # Unwrap that envelope before Pydantic validates the analysis response.
        if (
            isinstance(parsed, dict)
            and parsed.get("name") == "json"
            and "arguments" in parsed
        ):
            arguments = parsed["arguments"]
            if isinstance(arguments, dict):
                return json.dumps(arguments, ensure_ascii=False)
            if isinstance(arguments, str):
                return arguments
        return payload
    return cleaned
