"""
This file will contain chat-related API endpoints.

Why it exists:
We keep chat routes separate so the API structure stays clean and easy
to grow as the project gets more features.
"""

import logging

from fastapi import APIRouter, HTTPException, status
from google.api_core.exceptions import ResourceExhausted

from app.models.schemas import ChatRequest, ChatResponse
from app.services.llm_factory import get_chat_provider_order, get_llm

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Accept a user message, send it to the selected provider, and return the answer.
    
    Accepts:
        message: The user's chat message
        provider: LLM provider ("auto", "gemini", "groq")
        api_key: Optional user-provided API key
        temperature: Response creativity (0.0-1.0)
    """
    try:
        providers_to_try = get_chat_provider_order(request.provider)
    except RuntimeError as exc:
        logger.exception("Chat provider initialization failed.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    last_exception: Exception | None = None

    for index, provider in enumerate(providers_to_try):
        try:
            # Pass api_key and temperature from the request
            llm = get_llm(
                provider=provider,
                api_key=request.api_key,
                temperature=request.temperature,
            )
            llm_response = llm.invoke(request.message)
            return ChatResponse(
                answer=llm_response.content,
                provider=provider,
                fallback_used=index > 0,
            )
        except ResourceExhausted as exc:
            last_exception = exc
            logger.warning(
                "Quota exceeded for provider '%s'. Trying next provider if available.",
                provider,
            )
        except RuntimeError as exc:
            last_exception = exc
            logger.warning(
                "Initialization failed for provider '%s'. Trying next provider if available.",
                provider,
            )
        except Exception as exc:
            last_exception = exc
            logger.exception(
                "Chat request failed for provider '%s'. Trying next provider if available.",
                provider,
            )

    if isinstance(last_exception, ResourceExhausted):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="All configured chat providers are rate-limited right now.",
        ) from last_exception

    if isinstance(last_exception, RuntimeError):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No configured chat provider could be initialized.",
        ) from last_exception

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to generate chat response from all configured providers.",
    ) from last_exception
