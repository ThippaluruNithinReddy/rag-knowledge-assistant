# Setup Guide

This guide helps a new developer clone, configure, and verify Knowledge Assistant from scratch.

## Prerequisites

- Python 3.11
- `pip`
- `git`

Optional but recommended:
- a dedicated virtual environment
- VS Code or another Python-friendly editor

## 1. Clone The Repository

```bash
git clone https://github.com/ThippaluruNithinReddy/rag-knowledge-assistant.git
cd rag-knowledge-assistant
```

## 2. Create A Virtual Environment

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Mac/Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Create Local Environment Configuration

Copy `.env.example` to `.env`.

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### Mac/Linux

```bash
cp .env.example .env
```

## 5. Get API Keys

### Gemini
- Go to Google AI Studio.
- Create or select a project.
- Generate a Gemini API key.
- Paste it into `GEMINI_API_KEY` inside `.env`.

### Groq
- Go to the Groq console.
- Create an API key.
- Paste it into `GROQ_API_KEY` inside `.env`.

## 6. What Each `.env` Variable Does

| Variable | What it does |
|---|---|
| `GEMINI_API_KEY` | Authenticates Gemini requests |
| `GEMINI_LLM_MODEL` | Selects the Gemini chat model |
| `GEMINI_EMBEDDING_MODEL` | Selects the Gemini embedding model when Gemini embeddings are enabled |
| `GROQ_API_KEY` | Authenticates Groq requests |
| `GROQ_LLM_MODEL` | Selects the Groq-served model |
| `DEFAULT_CHAT_PROVIDER` | Default mode for chat and RAG provider ordering |
| `PRIMARY_CHAT_PROVIDER` | First provider to try |
| `FALLBACK_CHAT_PROVIDER` | Second provider to try if the first fails |
| `EMBEDDING_PROVIDER` | Chooses `huggingface` or `gemini` embeddings |

## 7. Run The Application

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## 8. Verify Setup

The quickest verification path is:

1. Start the server.
2. Open `http://127.0.0.1:8000/docs`.
3. Call `GET /`.
4. Confirm the response is:

```json
{"status": "ok"}
```

Then test:
- `POST /upload`
- `POST /rag/ask`

## 9. First-Run Notes

If `EMBEDDING_PROVIDER=huggingface`, the embedding model may download on first use. That is normal. The first upload request can take longer than later runs because the local model has to be prepared.

## Common Errors And Fixes

### Python version is wrong
Problem:
- packages may fail to install
- runtime behavior may differ from the intended environment

Fix:
- confirm `python --version` or `python3 --version`
- use Python 3.11
- recreate the virtual environment after switching versions

### Package conflicts
Problem:
- imports fail
- version mismatch warnings appear
- installation partially succeeds

Fix:
- remove the current virtual environment
- recreate it fresh
- reinstall with `pip install -r requirements.txt`

### API key not working
Problem:
- requests fail during chat or RAG generation
- provider initialization errors appear

Fix:
- confirm the key is copied correctly into `.env`
- restart the server after changing `.env`
- verify the correct provider is enabled in the config fields

### HuggingFace model download is slow on first run
Problem:
- the first embedding request takes longer than expected

Fix:
- wait for the initial download to finish
- keep the machine online during the first run
- retry the upload after the model has been cached locally

## Helpful Next Checks

After setup succeeds, a good manual validation flow is:

1. Upload a real PDF or TXT document.
2. Ask one question that is clearly answered in the document.
3. Ask one question that is clearly not in the document.
4. Confirm:
   - the answer is grounded in the document
   - the source filename is returned
   - the `answerable` flag changes correctly
