"""
This file splits loaded documents into smaller chunks for retrieval.

Why it exists:
RAG works better when large documents are broken into smaller, overlapping
pieces that can be embedded and searched more accurately.
"""

import logging

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings

logger = logging.getLogger(__name__)


def chunk_documents(
    documents: list[Document],
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> tuple[list[Document], int, int]:
    """
    Split loaded documents into smaller overlapping chunks.
    
    Returns:
        Tuple of (chunks, resolved_chunk_size, resolved_chunk_overlap)
        This allows the caller to know what settings were actually used.
    """
    # Resolve to parameters passed, then settings, then hardcoded defaults
    resolved_size = chunk_size if chunk_size is not None else (settings.chunk_size or 1000)
    resolved_overlap = chunk_overlap if chunk_overlap is not None else (settings.chunk_overlap or 200)
    
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=resolved_size,
            chunk_overlap=resolved_overlap,
        )

        # LangChain keeps document metadata when splitting, including source.
        chunks = text_splitter.split_documents(documents)

        logger.info(
            "Created %s chunk(s) from %s document(s) with chunk_size=%s, overlap=%s.",
            len(chunks),
            len(documents),
            resolved_size,
            resolved_overlap,
        )
        return chunks, resolved_size, resolved_overlap
    except Exception as exc:
        logger.exception("Failed to split documents into chunks.")
        raise RuntimeError(f"Could not chunk documents: {exc}") from exc
