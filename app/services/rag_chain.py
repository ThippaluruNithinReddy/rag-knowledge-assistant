"""
This file runs the retrieval-augmented generation flow for document questions.

Why it exists:
RAG needs one place that takes a user question, retrieves the most relevant
document chunks from FAISS, builds the prompt, calls the LLM, and returns
the final answer with source filenames.
"""

import logging

from google.api_core.exceptions import ResourceExhausted
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate

from app.config import settings
from app.services.llm_factory import get_chat_provider_order, get_llm
from app.services.vector_store import search

logger = logging.getLogger(__name__)

NO_ANSWER_TEXT = "I cannot find the answer to this in the provided documents."
RAG_PROMPT_TEMPLATE = """You are a helpful assistant that answers questions from company documents.
Answer using ONLY the context below.
If the answer is not in the context, respond with exactly this phrase:
"I cannot find the answer to this in the provided documents."
Do not guess. Do not use outside knowledge. Do not add anything extra.

Context:
{context}

Question:
{question}

Answer:
"""


def run_rag(
    question: str,
    store: FAISS,
    provider: str = "auto",
    api_key: str | None = None,
    temperature: float = 0.7,
    top_k: int = 4,
) -> dict:
    """
    Retrieve the most relevant chunks and generate an answer using only them.
    
    Parameters:
        question: User's question about the document
        store: FAISS vector store with document chunks
        provider: LLM provider ("auto", "gemini", "groq")
        api_key: Optional user-provided API key
        temperature: Response creativity (0.0-1.0)
        top_k: Number of chunks to retrieve for context
    
    Returns:
        Dict with keys: answer, sources, answerable, provider, fallback_used
    """
    try:
        # Retrieve the most relevant chunks based on top_k parameter
        retrieved_chunks = search(store, question, k=top_k)

        context = "\n\n".join(chunk.page_content for chunk in retrieved_chunks)
        prompt = PromptTemplate.from_template(RAG_PROMPT_TEMPLATE).format(
            context=context,
            question=question,
        )

        sources = list(
            dict.fromkeys(
                chunk.metadata.get("source")
                for chunk in retrieved_chunks
                if chunk.metadata.get("source")
            )
        )

        providers_to_try = get_chat_provider_order(provider)
        last_exception: Exception | None = None

        for provider_attempt in providers_to_try:
            try:
                # Pass api_key and temperature to get_llm
                llm = get_llm(
                    provider=provider_attempt,
                    api_key=api_key,
                    temperature=temperature,
                )
                llm_response = llm.invoke(prompt)
                answer = str(llm_response.content).strip()

                logger.info(
                    "Generated RAG answer using provider '%s' with %s retrieved chunk(s) and top_k=%s.",
                    provider_attempt,
                    len(retrieved_chunks),
                    top_k,
                )
                return {
                    "answer": answer,
                    "sources": sources,
                    "answerable": NO_ANSWER_TEXT not in answer,
                    "provider": provider_attempt,
                    "fallback_used": provider_attempt != providers_to_try[0],
                }
            except ResourceExhausted as exc:
                last_exception = exc
                logger.warning(
                    "RAG provider '%s' hit a rate limit. Trying next provider if available.",
                    provider_attempt,
                )
            except Exception as exc:
                last_exception = exc
                logger.exception(
                    "RAG generation failed for provider '%s'. Trying next provider if available.",
                    provider_attempt,
                )

        if last_exception is not None:
            raise last_exception

        raise RuntimeError("No configured chat provider was available for RAG.")
    except Exception as exc:
        logger.exception("Failed to run RAG chain.")
        raise RuntimeError(f"Could not generate RAG answer: {exc}") from exc
