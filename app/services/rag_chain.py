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


def run_rag(question: str, store: FAISS) -> dict:
    """
    Retrieve the most relevant chunks and generate an answer using only them.
    """
    try:
        retrieved_chunks = search(store, question, k=4)

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

        providers_to_try = get_chat_provider_order(settings.default_chat_provider)
        last_exception: Exception | None = None

        for provider in providers_to_try:
            try:
                llm = get_llm(provider)
                llm_response = llm.invoke(prompt)
                answer = str(llm_response.content).strip()

                logger.info(
                    "Generated RAG answer using provider '%s' with %s retrieved chunk(s).",
                    provider,
                    len(retrieved_chunks),
                )
                return {
                    "answer": answer,
                    "sources": sources,
                    "answerable": NO_ANSWER_TEXT not in answer,
                }
            except ResourceExhausted as exc:
                last_exception = exc
                logger.warning(
                    "RAG provider '%s' hit a rate limit. Trying next provider if available.",
                    provider,
                )
            except Exception as exc:
                last_exception = exc
                logger.exception(
                    "RAG generation failed for provider '%s'. Trying next provider if available.",
                    provider,
                )

        if last_exception is not None:
            raise last_exception

        raise RuntimeError("No configured chat provider was available for RAG.")
    except Exception as exc:
        logger.exception("Failed to run RAG chain.")
        raise RuntimeError(f"Could not generate RAG answer: {exc}") from exc
