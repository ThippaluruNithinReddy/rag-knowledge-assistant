"""
This file contains RAG-related API endpoints.

Why it exists:
We keep document upload and retrieval-based question answering routes
separate from basic chat routes so the document workflow stays clean,
testable, and easy to understand.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.models.schemas import DocumentUploadResponse, RAGRequest, RAGResponse
from app.services.chunker import chunk_documents
from app.services.document_loader import load_document
from app.services.rag_chain import run_rag
from app.services.vector_store import create_and_save_store, load_store

router = APIRouter(tags=["rag"])

logger = logging.getLogger(__name__)

UPLOADS_DIR = Path("data/uploads")
FAISS_INDEX_DIR = Path("faiss_index")
SUPPORTED_UPLOAD_EXTENSIONS = {".pdf", ".txt"}


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    """
    Save an uploaded document, load it, chunk it, and build the FAISS index.
    """
    original_filename = file.filename or ""
    safe_filename = Path(original_filename).name
    file_extension = Path(safe_filename).suffix.lower()

    if file_extension not in SUPPORTED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and TXT files are supported",
        )

    try:
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        saved_file_path = UPLOADS_DIR / safe_filename

        file_bytes = await file.read()
        saved_file_path.write_bytes(file_bytes)

        documents = load_document(str(saved_file_path))
        chunks = chunk_documents(documents)
        create_and_save_store(chunks, str(FAISS_INDEX_DIR))

        logger.info(
            "Uploaded and indexed document '%s' into %s chunk(s).",
            safe_filename,
            len(chunks),
        )
        return DocumentUploadResponse(
            filename=safe_filename,
            chunks_created=len(chunks),
            message="Document uploaded and indexed successfully",
        )
    except ValueError as exc:
        logger.exception("Upload validation failed for file '%s'.", safe_filename)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Document upload and indexing failed for '%s'.", safe_filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process uploaded document: {exc}",
        ) from exc
    finally:
        await file.close()


@router.post(
    "/rag/ask",
    response_model=RAGResponse,
    status_code=status.HTTP_200_OK,
)
def ask_rag_question(request: RAGRequest) -> RAGResponse:
    """
    Load the FAISS index and answer a document question using RAG.
    """
    try:
        store = load_store(str(FAISS_INDEX_DIR))
        result = run_rag(request.question, store)
        return RAGResponse(**result)
    except FileNotFoundError as exc:
        logger.exception("RAG question asked before any document was indexed.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No document uploaded yet. Please upload a document first.",
        ) from exc
    except RuntimeError as exc:
        logger.exception("RAG request failed during retrieval or generation.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
