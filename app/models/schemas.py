"""
This file defines the request and response data models used by the API.

Why it exists:
We need a clear and validated structure for the data that comes into
the API and the data that goes out of it. FastAPI uses these models to
validate requests, shape responses, and generate API documentation.
"""

from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """
    Request body for the basic chat endpoint.
    """

    message: str = Field(..., description="The user's chat message.")
    provider: Literal["auto", "gemini", "groq"] = Field(
        default="auto",
        description="The LLM provider to use for this chat request.",
    )


class ChatResponse(BaseModel):
    """
    Response body returned by the basic chat endpoint.
    """

    answer: str = Field(..., description="The answer returned by the model.")
    provider: str = Field(..., description="The model provider name.")
    fallback_used: bool = Field(
        ..., description="Whether the response came from a fallback provider."
    )


class RAGRequest(BaseModel):
    """
    Request body for asking a question over uploaded documents.
    """

    question: str = Field(..., description="The user's question about the document.")


class RAGResponse(BaseModel):
    """
    Response body returned by the RAG question-answering endpoint.
    """

    answer: str = Field(..., description="The answer generated from retrieved context.")
    sources: list[str] = Field(
        ..., description="The source filenames used to generate the answer."
    )
    answerable: bool = Field(
        ..., description="Whether the system found enough context to answer."
    )


class DocumentUploadResponse(BaseModel):
    """
    Response body returned after a document is uploaded and processed.
    """

    filename: str = Field(..., description="The uploaded document filename.")
    chunks_created: int = Field(
        ..., description="The number of chunks created from the document."
    )
    message: str = Field(..., description="A short status message about the upload.")
