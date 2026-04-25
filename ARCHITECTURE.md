# Architecture

This document explains the internal structure of Knowledge Assistant in more depth than the README.

## System Components

### `app/main.py`
This file creates the FastAPI application object and registers the route modules. It is the entry point for the API server and keeps the startup wiring in one place so the rest of the code can stay focused on business logic.

### `app/config.py`
This file centralizes configuration using `pydantic-settings`. It maps environment variables from `.env` into typed Python settings so the rest of the application can read configuration safely and consistently without hardcoding secrets or provider names.

### `app/models/schemas.py`
This file defines the request and response bodies used by the API. FastAPI uses these schemas for validation, API documentation generation, and response shaping, which makes the external contract of the system explicit.

### `app/routes/chat.py`
This file exposes the direct LLM chat endpoint. It handles request validation, chooses provider order through `llm_factory.py`, applies fallback behavior when a provider fails or hits a rate limit, and returns a normalized chat response.

### `app/routes/rag.py`
This file exposes the document upload and retrieval-based question-answering endpoints. It is responsible for receiving uploads, saving them to disk, orchestrating indexing, loading the vector store for questions, and translating internal exceptions into HTTP responses.

### `app/services/llm_factory.py`
This file is the provider abstraction layer. It creates Gemini or Groq chat models, determines provider order for fallback behavior, and returns the configured embedding implementation. By keeping provider creation in one place, the rest of the codebase remains provider-agnostic.

### `app/services/document_loader.py`
This file loads supported document types into LangChain `Document` objects. It handles PDF and TXT loading, normalizes metadata so the source filename is preserved, and gives the rest of the pipeline a consistent structure regardless of file type.

### `app/services/chunker.py`
This file splits loaded documents into smaller overlapping chunks using `RecursiveCharacterTextSplitter`. It preserves metadata while making the text easier to embed and retrieve accurately.

### `app/services/vector_store.py`
This file creates, saves, loads, and searches the FAISS vector store. It is responsible for turning chunk text into embeddings through the configured embedding provider and making the resulting vectors searchable.

### `app/services/rag_chain.py`
This file coordinates the RAG answer generation step. It retrieves the most relevant chunks from FAISS, builds the prompt using the required grounding instructions, calls the configured LLM with fallback behavior, and returns the final structured answer.

## RAG Pipeline Explained

### Phase 1 - Indexing

```text
Document -> Load -> Chunk -> Embed -> Store in FAISS
```

This phase happens during document upload. The uploaded file is saved to disk, loaded into LangChain documents, split into overlapping chunks, embedded into vectors, and persisted locally inside the FAISS index directory. The result is a searchable local index that can be reused without reprocessing the file after every restart.

### Phase 2 - Retrieval

```text
Question -> Embed -> Search FAISS -> Retrieve chunks -> Build prompt -> LLM -> Answer
```

This phase happens for every RAG question. The user’s question is converted into the same vector space as the document chunks, FAISS returns the most similar chunks, and those chunks are inserted into the prompt as the only allowed context for the LLM. The model then produces the final answer plus source filenames and the `answerable` flag.

## Why Each Technology Was Chosen

### FastAPI
FastAPI was chosen because it gives strong request validation, clear automatic API docs, and a clean development workflow for building JSON and file-upload APIs. Alternatives include Flask, Django REST Framework, and Starlette directly. FastAPI fits well here because the project needs typed request models, multipart upload support, and quick interactive testing through `/docs`.

### LangChain
LangChain was chosen because it provides standardized abstractions for document loaders, chunkers, embeddings, vector stores, and model integrations. Alternatives include building all orchestration manually or using frameworks such as LlamaIndex. LangChain is a practical fit here because it reduces boilerplate while still exposing the components clearly enough for learning and customization.

### FAISS
FAISS was chosen as the local vector store because it is fast, well-known, and easy to run without external infrastructure. Alternatives include ChromaDB, Qdrant, Weaviate, Pinecone, and Elasticsearch vector search. FAISS is a good fit for a single-user or early-stage project because it keeps the stack simple and local.

### HuggingFace Embeddings
HuggingFace embeddings were chosen as the default because they run locally, avoid API costs during development, and remove rate-limit dependency for retrieval. Alternatives include Gemini embeddings, OpenAI embeddings, or a hosted embedding endpoint. The local `all-MiniLM-L6-v2` model is a strong development default because it is lightweight and easy to reproduce.

### Groq Fallback
Groq was chosen as a fallback LLM provider to improve resilience when Gemini is unavailable, slow, or rate-limited. Alternatives include relying on a single provider or adding another hosted LLM such as OpenAI or Anthropic. A fallback path keeps the chat and RAG flows more robust without changing the rest of the application contract.

## Multi-Provider Design

`llm_factory.py` exists so every LLM-related call passes through one provider selection layer. `get_llm()` hides the details of how Gemini and Groq clients are initialized, `get_chat_provider_order()` decides which provider order to use for a request, and `get_embeddings()` hides whether embeddings come from Gemini or HuggingFace.

This design matters because routes and services should not care about provider-specific client setup. They should only ask for “an LLM” or “an embedding model” and continue their own job. That keeps provider logic centralized and makes the application easier to maintain.

To add a new provider, the main changes would happen in `llm_factory.py`: add the provider to the supported set, implement initialization logic, extend provider-order handling if needed, and add any required configuration fields in `app/config.py` and `.env.example`. The rest of the system could continue calling the same factory functions.

## Failure Handling

### Document cannot be loaded
This can happen because of an unsupported file type, a corrupted file, missing file path, or parsing failure. Currently, `document_loader.py` catches the underlying exception, logs it, and raises a clear runtime error that the API route turns into an HTTP error response.

### Embedding model not downloaded yet
When HuggingFace embeddings are used for the first time, the local model download can take noticeable time. Currently, the system waits during embedding initialization. If that download fails because of connectivity or package issues, the vector store creation step raises an exception and the upload request fails clearly.

### FAISS index does not exist
If a question is asked before any document has been uploaded and indexed, `vector_store.py` raises a `FileNotFoundError` with a clear message. The RAG route converts that into an HTTP 400 response telling the user to upload a document first.

### LLM rate limit hit
If Gemini or Groq hits a rate limit, the system uses the provider-order logic to try the next configured provider. This behavior is already present in direct chat and is also applied in the RAG chain. If all providers fail, the request returns a clear error instead of silently hanging.

### Question is unanswerable from the document
If the retrieved context does not contain the answer, the prompt instructs the LLM to return a fixed not-found sentence. The code then checks for that sentence and sets `answerable` to `false`, making unanswerable questions explicit in the API response.

## Limitations And Future Improvements

The current system stores only one active FAISS index, which means a new upload replaces the effective working set instead of supporting multiple named document spaces. A production-grade multi-user version would need document-level indexing, user or tenant separation, and more careful lifecycle management of stored files.

The chunking strategy is intentionally simple and character-based. It works well for plain text and straightforward PDFs but is not optimized for tables, forms, or layout-heavy documents. Future work could introduce semantic chunking, table-aware parsing, or page-structure preservation.

The FAISS index is local to the server filesystem, which is convenient for development but not ideal for distributed or autoscaled deployments. A more production-ready architecture would likely move retrieval into a dedicated vector database and store document metadata in a persistent application database.

The current RAG flow also has no reranking layer. Retrieval quality depends entirely on chunking and first-pass similarity search. Adding a reranker or cross-encoder after FAISS retrieval would help filter noisy chunks before the prompt is constructed.
