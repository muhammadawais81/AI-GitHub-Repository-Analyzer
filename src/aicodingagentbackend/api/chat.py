"""Chat API routes powered by the RAG Coding Review Agent."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from aicodingagentbackend.core.dependencies import get_agent_service
from aicodingagentbackend.schemas.chat import ChatRequest, ChatResponse
from aicodingagentbackend.services.agent_service import AgentService

router = APIRouter(tags=["chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask the Coding Review Agent about an indexed repository",
    description=(
        "Retrieves the top semantic chunks from ChromaDB for the question, then "
        "runs the Coding Review Agent (Groq via OpenAI-compatible API). The agent may call "
        "retrieve_relevant_chunks again or read_file only when needed."
    ),
)
async def chat(
    payload: ChatRequest,
    service: AgentService = Depends(get_agent_service),
) -> ChatResponse:
    return await service.ask(payload.repository_name, payload.question)
