"""
This file creates, saves, loads, and searches the FAISS vector store.

Why it exists:
RAG needs a fast way to store chunk embeddings and retrieve the most
relevant chunks for a user's question without re-embedding on every run.
"""

import logging
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.services.llm_factory import get_embeddings

logger = logging.getLogger(__name__)


def create_and_save_store(chunks: list[Document], store_path: str) -> FAISS:
    """
    Create a FAISS store from document chunks and save it to disk.
    """
    try:
        if not chunks:
            raise ValueError("No chunks were provided to create the vector store.")

        embeddings = get_embeddings()
        vector_store = FAISS.from_documents(chunks, embeddings)

        # Ensure the target directory exists before saving the index files.
        Path(store_path).mkdir(parents=True, exist_ok=True)
        vector_store.save_local(store_path)

        logger.info("Created and saved FAISS index to %s.", store_path)
        return vector_store
    except Exception as exc:
        logger.exception("Failed to create and save FAISS store.")
        raise RuntimeError(f"Could not create and save vector store: {exc}") from exc


def load_store(store_path: str) -> FAISS:
    """
    Load an existing FAISS store from disk.
    """
    try:
        store_directory = Path(store_path)
        if not store_directory.exists():
            raise FileNotFoundError(
                "No document index found. Please upload a document first."
            )

        # LangChain FAISS saves these files in the target folder.
        if not (store_directory / "index.faiss").exists() or not (
            store_directory / "index.pkl"
        ).exists():
            raise FileNotFoundError(
                "No document index found. Please upload a document first."
            )

        embeddings = get_embeddings()
        vector_store = FAISS.load_local(
            folder_path=store_path,
            embeddings=embeddings,
            allow_dangerous_deserialization=True,
        )

        logger.info("Loaded FAISS index from %s.", store_path)
        return vector_store
    except FileNotFoundError:
        raise
    except Exception as exc:
        logger.exception("Failed to load FAISS store from %s.", store_path)
        raise RuntimeError(f"Could not load vector store: {exc}") from exc


def search(store: FAISS, query: str, k: int = 4) -> list[Document]:
    """
    Search the FAISS store and return the top matching chunks.
    """
    try:
        results = store.similarity_search(query, k=k)
        logger.info("Found %s similar chunk(s) for the query.", len(results))
        return results
    except Exception as exc:
        logger.exception("Failed to search FAISS store.")
        raise RuntimeError(f"Could not search vector store: {exc}") from exc
