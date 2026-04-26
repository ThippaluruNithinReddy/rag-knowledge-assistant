"""
This file creates and returns the AI objects used by the application.

Why it exists:
We need one central place to configure and create the Gemini chat model
and Gemini embeddings model. This keeps the setup clean and avoids
repeating the same code in many files.
"""

import logging

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings,
)
from langchain_groq import ChatGroq

from app.config import settings

logger = logging.getLogger(__name__)

SUPPORTED_CHAT_PROVIDERS = {"gemini", "groq"}


def get_llm(
    provider: str = "gemini",
    api_key: str | None = None,
    temperature: float = 0.7,
) -> BaseChatModel:
    """
    Create and return the selected chat model with resolved credentials and temperature.
    
    Priority for values:
    1. Parameters passed to this function (from request)
    2. Values from settings (from .env)
    3. Hardcoded defaults
    """
    try:
        if provider == "gemini":
            resolved_key = api_key or settings.gemini_api_key
            if not resolved_key:
                raise ValueError("Gemini API key not provided")
            return ChatGoogleGenerativeAI(
                model=settings.gemini_llm_model,
                google_api_key=resolved_key,
                temperature=temperature,
            )
        if provider == "groq":
            resolved_key = api_key or settings.groq_api_key
            if not resolved_key:
                raise ValueError("Groq API key not provided")

            return ChatGroq(
                model=settings.groq_llm_model,
                api_key=resolved_key,
                temperature=temperature,
            )

        raise ValueError(f"Unsupported provider: {provider}")
    except Exception as exc:
        logger.exception(
            "Failed to create chat model for provider '%s' with temperature %.1f.",
            provider,
            temperature,
        )
        raise RuntimeError(f"Could not initialize the '{provider}' chat model.") from exc


def get_chat_provider_order(provider: str) -> list[str]:
    """
    Return the ordered list of chat providers to try for a request.
    """
    if provider == "auto":
        ordered_providers = [
            settings.primary_chat_provider,
            settings.fallback_chat_provider,
        ]

        # Remove duplicates while preserving order.
        unique_providers = list(dict.fromkeys(ordered_providers))
        invalid_providers = [
            item for item in unique_providers if item not in SUPPORTED_CHAT_PROVIDERS
        ]
        if invalid_providers:
            raise RuntimeError(
                "Invalid chat provider configuration: "
                + ", ".join(invalid_providers)
            )
        return unique_providers

    if provider not in SUPPORTED_CHAT_PROVIDERS:
        raise RuntimeError(f"Unsupported provider: {provider}")

    return [provider]


def get_embeddings():
    provider = settings.embedding_provider.lower()

    if provider == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(
            model=settings.gemini_embedding_model,
            google_api_key=settings.gemini_api_key,
        )
    else:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )
