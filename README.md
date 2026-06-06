# Medical RAG System — Deployable Edition

Multi-agent RAG system for **educational medical information** with a FastAPI backend, React frontend, FAISS vector store, and **OpenRouter** for LLM inference.

> **Safety:** This system does not prescribe medicines or provide dosing instructions.

## What you need from OpenRouter

Only **one API key** is required for chat:

| Purpose | Provider | API needed? |
|---------|----------|-------------|
| Doctor + Supervisor LLM | OpenRouter | **Yes** — `OPENROUTER_API_KEY` |
| Embeddings (PDF search) | Local CPU (`sentence-transformers`) | **No** — runs free on your server |

Optional: set `EMBEDDING_PROVIDER=openrouter` and use `openai/text-embedding-3-small` if you prefer cloud embeddings (costs apply per document chunk).

### Recommended OpenRouter models (in `config.yaml`)

```yaml
models:
  doctor: meta-llama/llama-3.2-3b-instruct
  supervisor: meta-llama/llama-3.2-3b-instruct
```

Other good options: `google/gemma-2-9b-it`, `deepseek/deepseek-r1-distill-llama-8b`, `mistralai/mistral-7b-instruct`.

Get your key: https://openrouter.ai/keys

---

## Deploy to Vercel

Frontend on **Vercel**, backend on **Railway** or **Render**. See **[DEPLOYMENT.md](DEPLOYMENT.md)** for the full guide.

---

## Quick start (local)

### 1. Backend

```powershell
cd medical-rag-system
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `.env` and set your key:

```powershell
copy .env.example .env
# Edit .env → set OPENROUTER_API_KEY=sk-or-v1-...
```

### 3. Build knowledge base (first run)

Indexes all PDFs in `data/pdfs/` plus other `data/` folders:

```powershell
python scripts/build_kb.py
```

### 4. Run backend

```powershell
$env:DISABLE_AUTH = "1"
uvicorn app:api --reload --port 8000
```

### 5. Run frontend (dev)

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — API calls proxy to port 8000.

---

## Production (single server)

Build frontend and serve everything from FastAPI:

```powershell
cd frontend
npm install
npm run build
cd ..
uvicorn app:api --host 0.0.0.0 --port 8000
```

Open http://localhost:8000

---

## Docker deploy

```powershell
copy .env.example .env
# Set OPENROUTER_API_KEY in .env

docker compose up --build
```

App available at http://localhost:8000

---

## Knowledge base PDFs included

- `data/pdfs/Emergency Medicine.pdf`
- `data/pdfs/NRS Emergency Medicine Protocols.pdf`
- `data/pdfs/ENT OPD CASES MANAGEMENT...pdf`
- `data/pdfs/WARD ADVICE U3 GENERAL MEDICINE NRSMCH.pdf`
- `data/pdfs/Medical RAG System.pdf`

Add more PDFs to `data/pdfs/` and run `python scripts/build_kb.py` to rebuild.

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | — | **Required** for LLM chat |
| `LLM_PROVIDER` | `openrouter` | `openrouter` or `ollama` |
| `EMBEDDING_PROVIDER` | `local` | `local`, `openrouter`, or `ollama` |
| `DISABLE_AUTH` | `1` | Skip Firebase auth for demo |
| `GOOGLE_APPLICATION_CREDENTIALS` | — | Firebase JSON (if auth enabled) |

---

## API endpoints

- `GET /healthz` — service status, KB readiness, LLM connectivity
- `POST /api/medical/analyze` — multipart form: `user_input`, `input_type`, optional `file`
- `GET /` — React UI (production build)

---

## Architecture

```
User → React UI → FastAPI
                    ├─ Gatekeeper (safety / PII)
                    ├─ Doctor (RAG + OpenRouter LLM)
                    └─ Supervisor (review + OpenRouter LLM)
                         ↕
                    FAISS vector store ← local embeddings
                         ↕
                    data/pdfs/*.pdf
```
