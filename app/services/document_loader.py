"""
This file loads supported documents into LangChain Document objects.

Why it exists:
The RAG pipeline needs one consistent way to read different file types
like PDF and TXT files and attach source metadata for later citation.
"""

import logging
from pathlib import Path

from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".txt"}


def load_document(file_path: str) -> list[Document]:
    """
    Load a PDF or TXT file and return LangChain Document objects.
    """
    try:
        path = Path(file_path)
        extension = path.suffix.lower()
        filename = path.name

        if not path.exists():
            raise FileNotFoundError(f"File not found: {filename}")

        if extension not in SUPPORTED_EXTENSIONS:
            raise ValueError("Only PDF and TXT files are supported.")

        if extension == ".pdf":
            loader = PyPDFLoader(str(path))
        else:
            # UTF-8 is the safest default for plain text files in this project.
            loader = TextLoader(str(path), encoding="utf-8")

        documents = loader.load()

        for document in documents:
            # Keep any existing metadata and add the filename as the source.
            document.metadata = {**document.metadata, "source": filename}

        logger.info("Loaded %s document section(s) from %s.", len(documents), filename)
        return documents
    except Exception as exc:
        logger.exception("Failed to load document: %s", file_path)
        raise RuntimeError(f"Could not load document '{Path(file_path).name}': {exc}") from exc
