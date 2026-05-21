"""
This file contains RAG-related API endpoints.

Why it exists:
We keep document upload and retrieval-based question answering routes
separate from basic chat routes so the document workflow stays clean,
testable, and easy to understand.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

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
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200),
) -> DocumentUploadResponse:
    """
    Save an uploaded document, load it, chunk it, and build the FAISS index.
    
    Form fields:
        file: PDF or TXT file to upload
        chunk_size: Characters per chunk (default 1000)
        chunk_overlap: Overlap between chunks (default 200)
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
        # chunk_documents now returns tuple of (chunks, used_size, used_overlap)
        chunks, used_chunk_size, used_chunk_overlap = chunk_documents(
            documents,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        create_and_save_store(chunks, str(FAISS_INDEX_DIR))

        logger.info(
            "Uploaded and indexed document '%s' into %s chunk(s) with size=%s, overlap=%s.",
            safe_filename,
            len(chunks),
            used_chunk_size,
            used_chunk_overlap,
        )
        return DocumentUploadResponse(
            filename=safe_filename,
            chunks_created=len(chunks),
            chunk_size=used_chunk_size,
            chunk_overlap=used_chunk_overlap,
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
    
    Accepts:
        question: The user's question
        provider: LLM provider ("auto", "gemini", "groq")
        api_key: Optional user-provided API key
        temperature: Response creativity (0.0-1.0)
        top_k: Number of document chunks to use for context
    """
    try:
        store = load_store(str(FAISS_INDEX_DIR))
        result = run_rag(
            question=request.question,
            store=store,
            provider=request.provider,
            api_key=request.api_key,
            temperature=request.temperature,
            top_k=request.top_k,
        )
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
