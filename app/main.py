"""
This file creates the FastAPI application and registers the API routes.

Why it exists:
FastAPI needs one central application object to run the server. This file
is the entry point of the API and connects route modules to the app.
"""

from fastapi import FastAPI

from app.routes.chat import router as chat_router
from app.routes.rag import router as rag_router

app = FastAPI(
    title="Knowledge Assistant API",
    version="1.0.0",
)


@app.get("/")
def health_check() -> dict[str, str]:
    """
    Simple health check endpoint to confirm the API is running.
    """
    return {"status": "ok"}


app.include_router(chat_router)
app.include_router(rag_router)
