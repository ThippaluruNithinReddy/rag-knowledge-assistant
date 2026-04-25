"""
This file loads application settings from environment variables.

Why it exists:
We need one clean place to read configuration like the Gemini API key.
This keeps secrets out of the code and makes configuration easy to manage.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from the .env file.

    Each class field maps to an environment variable.
    """

    gemini_api_key: str
    gemini_llm_model: str
    gemini_embedding_model: str
    groq_api_key: str | None = None
    groq_llm_model: str
    default_chat_provider: str = "auto"
    primary_chat_provider: str = "gemini"
    fallback_chat_provider: str = "groq"
    embedding_provider: str = "huggingface"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
