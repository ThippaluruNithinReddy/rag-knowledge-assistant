# RAG Implementation Guide

This file explains what has been built, why each part exists, and how to test the system end to end.

## What is completed

### Step 7 - Document loading
- File: `app/services/document_loader.py`
- Purpose:
  - read `.pdf` and `.txt` files from disk
  - convert them into LangChain `Document` objects
  - attach `metadata["source"]` with the filename

### Step 8 - Chunking
- File: `app/services/chunker.py`
- Purpose:
  - split loaded documents into smaller chunks
  - use `chunk_size=1000`
  - use `chunk_overlap=200`
  - preserve source metadata on each chunk

### Step 9 - Vector store
- File: `app/services/vector_store.py`
- Purpose:
  - create embeddings for chunks using `get_embeddings()`
  - store them in FAISS
  - save the FAISS index to disk
  - load the saved index later
  - search for the most similar chunks

### Step 10 - RAG chain
- File: `app/services/rag_chain.py`
- Purpose:
  - search FAISS for the top matching chunks
  - build the exact prompt
  - send prompt + retrieved context to the LLM
  - return `answer`, `sources`, and `answerable`

### Step 11 - RAG routes
- File: `app/routes/rag.py`
- Endpoints:
  - `POST /upload`
  - `POST /rag/ask`
- Purpose:
  - save uploaded files into `data/uploads/`
  - load, chunk, and index them
  - load the FAISS index and answer questions over the indexed document

## End-to-end flow

1. User uploads a PDF or TXT file.
2. FastAPI saves the file into `data/uploads/`.
3. `document_loader.py` reads the file into LangChain `Document` objects.
4. `chunker.py` splits the documents into smaller chunks.
5. `vector_store.py` converts chunks into embeddings and stores them in FAISS.
6. FAISS index files are saved into `faiss_index/`.
7. User asks a question with `POST /rag/ask`.
8. `vector_store.py` loads the FAISS index and finds the most relevant chunks.
9. `rag_chain.py` builds the prompt using only those chunks as context.
10. Gemini or Groq generates the answer.
11. The API returns:
    - `answer`
    - `sources`
    - `answerable`

## Important idea to remember

- The embedding model creates the semantic vectors.
- FAISS stores those vectors and searches them.
- The LLM does not search the document directly.
- The LLM only answers using the retrieved chunks.

## Files added or updated

- `app/services/document_loader.py`
- `app/services/chunker.py`
- `app/services/vector_store.py`
- `app/services/rag_chain.py`
- `app/routes/rag.py`
- `tests/test_loader_chunker.py`
- `.vscode/launch.json`

## How to run the API

From the project root:

```powershell
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## How to test manually

### Test 1 - Upload a document

Use `POST /upload`

- choose a PDF or TXT file
- expected result:
  - file saves into `data/uploads/`
  - chunks are created
  - FAISS index is saved into `faiss_index/`
  - response includes:
    - filename
    - chunks_created
    - `"Document uploaded and indexed successfully"`

### Test 2 - Ask a question that is in the document

Use `POST /rag/ask`

Example body:

```json
{
  "question": "What is the leave policy?"
}
```

Expected result:
- answer comes from the uploaded document
- `sources` contains the filename
- `answerable` is `true`

### Test 3 - Ask a question that is not in the document

Expected result:
- answer should be:
  - `"I cannot find the answer to this in the provided documents."`
- `answerable` should be `false`

### Test 4 - Ask a question that needs multiple sections

Expected result:
- answer may still work if the retrieved chunks contain enough context
- if it struggles, that gives us the next improvement area

## What to watch during testing

- Does upload reject unsupported file types correctly?
- Does the FAISS index folder contain `index.faiss` and `index.pkl`?
- Does `sources` show the correct filename?
- Does the answer avoid guessing?
- Does the system clearly say when the answer is not in the document?

## Current assumptions

- `.env` is already configured
- Gemini and/or Groq keys are available when needed
- `embedding_provider` is set correctly
- the local embedding model can be loaded if HuggingFace is used

## After testing

If something fails, the next place to inspect is usually:

- upload issue -> `app/routes/rag.py`
- file loading issue -> `app/services/document_loader.py`
- empty chunks issue -> `app/services/chunker.py`
- embedding or FAISS issue -> `app/services/vector_store.py`
- wrong answer issue -> `app/services/rag_chain.py`
