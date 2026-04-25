"""
This file splits loaded documents into smaller chunks for retrieval.

Why it exists:
RAG works better when large documents are broken into smaller, overlapping
pieces that can be embedded and searched more accurately.
"""

import logging

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def chunk_documents(documents: list[Document]) -> list[Document]:
    """
    Split loaded documents into smaller overlapping chunks.
    """
    try:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )

        # LangChain keeps document metadata when splitting, including source.
        chunks = text_splitter.split_documents(documents)

        logger.info(
            "Created %s chunk(s) from %s document(s).",
            len(chunks),
            len(documents),
        )
        return chunks
    except Exception as exc:
        logger.exception("Failed to split documents into chunks.")
        raise RuntimeError(f"Could not chunk documents: {exc}") from exc
