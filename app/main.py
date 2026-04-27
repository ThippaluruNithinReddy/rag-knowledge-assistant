"""
This file creates the FastAPI application and registers the API routes.

Why it exists:
FastAPI needs one central application object to run the server. This file
is the entry point of the API and connects route modules to the app.
"""

import os
import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.chat import router as chat_router
from app.routes.rag import router as rag_router

app = FastAPI(
    title="Knowledge Assistant API",
    version="1.0.0",
)

# Environment-aware configuration
app_env = os.getenv("APP_ENV", "development")

# Configure logging for production
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)
logger.info(f"Starting Knowledge Assistant API — env: {app_env}")

# CORS: restrict in production using FRONTEND_URL, otherwise allow all in development
if app_env == "production":
    allowed_origins = [os.getenv("FRONTEND_URL", "*")]
else:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure runtime directories exist (Render provides fresh filesystem on each start)
os.makedirs("data/uploads", exist_ok=True)
os.makedirs("faiss_index", exist_ok=True)
logger.info("Required directories verified: data/uploads, faiss_index")


@app.get("/")
def health_check() -> dict[str, str]:
    """
    Simple health check endpoint to confirm the API is running.
    """
    return {"status": "ok"}


app.include_router(chat_router)
app.include_router(rag_router)
