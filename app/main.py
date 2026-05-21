"""
This file creates the FastAPI application and registers the API routes.

Why it exists:
FastAPI needs one central application object to run the server. This file
is the entry point of the API and connects route modules to the app.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routes.chat import router as chat_router
from app.routes.rag import router as rag_router

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
FRONTEND_INDEX = FRONTEND_DIR / "index.html"

app = FastAPI(
    title="Knowledge Assistant API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    """
    Simple health check endpoint to confirm the API is running.
    """
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def serve_frontend() -> FileResponse:
    """
    Serve the existing frontend entry page from the FastAPI app.
    """
    return FileResponse(FRONTEND_INDEX)


if FRONTEND_DIR.exists():
    app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")


app.include_router(chat_router)
app.include_router(rag_router)
