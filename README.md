# Knowledge Assistant

An internal document question answering system powered by RAG.

## Problem It Solves

Company knowledge is often scattered across handbooks, policy documents, and internal guides. That makes it slow for employees to find answers and easy to miss the right source. Knowledge Assistant lets a user upload a document, ask questions against that document, and receive answers grounded in the actual content. When the answer is not present in the document, the system says so clearly instead of guessing.

## Architecture Overview

### Indexing flow

```text
User uploads document
  -> document_loader.py reads the file
  -> chunker.py splits into overlapping chunks
  -> vector_store.py embeds chunks and saves to FAISS
  -> FAISS index stored on disk
```

### Question answering flow

```text
User asks a question
  -> vector_store.py searches FAISS for top 4 relevant chunks
  -> rag_chain.py builds prompt with retrieved context
  -> LLM answers using only that context
  -> Response includes answer, source filename, and answerable flag
```

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| API Framework | FastAPI |
| AI Framework | LangChain |
| LLM Primary | Google Gemini |
| LLM Fallback | Groq (Llama 3.1 style fallback via Groq API) |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` (local) |
| Vector Store | FAISS (local) |
| Config | `pydantic-settings` |

## Project Structure

```text
knowledge-assistant/
├── app/                  # FastAPI app, routes, schemas, and RAG services
├── data/uploads/         # Runtime upload location for incoming documents
├── faiss_index/          # Runtime FAISS index storage
├── tests/                # Manual test helpers and sample documents
├── .env.example          # Safe template for local environment variables
├── requirements.txt      # Python dependencies
├── README.md             # Project overview and quick-start guide
├── ARCHITECTURE.md       # Deeper technical explanation of the system
└── SETUP.md              # First-time setup and troubleshooting guide
```

### Folder Guide

- `app/main.py` creates the FastAPI application and registers routes.
- `app/config.py` loads environment variables through `pydantic-settings`.
- `app/models/` contains request and response schemas.
- `app/routes/` exposes the HTTP API for chat, upload, and RAG question answering.
- `app/services/` contains the document loader, chunker, vector store, LLM factory, and RAG chain.
- `data/uploads/` stores uploaded documents at runtime and is intentionally excluded from Git.
- `faiss_index/` stores the generated vector index at runtime and is intentionally excluded from Git.
- `tests/` contains the manual loader/chunker test script and sample files.

## Setup Instructions

1. Clone the repository.
2. Create a Python 3.11 virtual environment.
3. Activate the virtual environment.
4. Install dependencies from `requirements.txt`.
5. Copy `.env.example` to `.env`.
6. Add your API keys and provider settings to `.env`.

## How To Run

```bash
uvicorn app.main:app --reload
```

Then open:

```text
http://localhost:8000/docs
```

## How To Use

1. Upload a document with `POST /upload`.
2. Ask a question with `POST /rag/ask`.
3. Read the answer, the source filename, and the `answerable` flag.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| POST | `/chat` | Direct LLM chat |
| POST | `/upload` | Upload and index a document |
| POST | `/rag/ask` | Ask a question from uploaded documents |

## Environment Variables

The running code currently uses the variables defined in `app/config.py` and `.env.example`.

| Variable | Description | Required |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `GEMINI_LLM_MODEL` | Gemini chat model name | Yes |
| `GEMINI_EMBEDDING_MODEL` | Gemini embedding model name | Yes if Gemini embeddings are used |
| `GROQ_API_KEY` | Groq API key for fallback | Yes for Groq fallback |
| `GROQ_LLM_MODEL` | Groq-served model name | Yes if Groq is used |
| `DEFAULT_CHAT_PROVIDER` | Default provider mode, usually `auto` | Yes |
| `PRIMARY_CHAT_PROVIDER` | Primary chat provider, such as `gemini` | Yes |
| `FALLBACK_CHAT_PROVIDER` | Fallback chat provider, such as `groq` | Yes |
| `EMBEDDING_PROVIDER` | `huggingface` or `gemini` | Yes |

If you prefer a simpler single-provider setup, `LLM_PROVIDER` can be thought of conceptually as the primary provider choice, but the current implementation uses explicit primary and fallback settings instead.

## Key Design Decisions

Multi-provider LLM support was built from the start so the system can stay usable when one provider is unavailable, rate-limited, or temporarily misconfigured. The `llm_factory.py` layer gives the rest of the application one consistent way to obtain an LLM without scattering provider-specific code across routes and services.

HuggingFace embeddings are the default because they run locally, avoid API rate limits, and keep retrieval cost predictable during development. This is especially useful for a project that needs a reliable baseline even when external API quotas are tight. Gemini embeddings remain available as a configurable option when managed embedding quality or hosted inference is preferred.

The `answerable` flag exists to make “not found in document” a first-class result instead of a vague natural-language guess. That makes the API easier to consume from a frontend and reduces ambiguity for users who need to know whether the answer was grounded in the uploaded document.

The chunk overlap of 200 characters helps preserve meaning at chunk boundaries. Without overlap, a sentence or condition can be split across two chunks and retrieval quality drops because neither chunk contains enough complete context on its own.

## Known Limitations

- Only one document index is active at a time.
- There is no conversation memory, so each question is treated independently.
- The fixed chunking strategy does not handle tables, forms, or other structured layouts especially well.
- FAISS is stored locally, which is fine for single-user or development workflows but not ideal for multi-user production deployment.

## Roadmap

- Multi-document support with per-document namespacing
- Conversation memory for follow-up questions
- Semantic chunking to improve retrieval quality
- Re-ranking retrieved chunks before sending them to the LLM
- Replacing FAISS with a managed or team-ready vector database such as ChromaDB or Pinecone
- Adding a frontend interface

## Deployment

This project can be deployed to Render (render.com) for demonstration and portfolio purposes.

**Live demo (example):** https://rag-knowledge-assistant-ui.onrender.com

**Known limitation:** The free tier of Render does not provide persistent disk storage. Uploaded documents
and the FAISS index are stored on the instance filesystem and will be lost when the service restarts
(for example, after periods of inactivity or when Render rebalances resources). For production usage,
migrate the vector store to a persistent solution such as PostgreSQL + pgvector.

**To use the live demo:**
1. Enter your own Gemini or Groq API key in the Settings panel in the UI.
2. Upload a PDF or TXT document.
3. Ask questions about your document.

