# Deployment Guide

This app has two parts:

| Part | Technology | Best platform |
|------|------------|---------------|
| **Frontend** (React UI) | Vite + React | **Vercel** |
| **Backend** (FastAPI + FAISS + embeddings) | Python | **Railway** or **Render** |

Vercel cannot run the Python knowledge-base server reliably (FAISS, large models, file storage). Deploy the API separately, then point the Vercel frontend at it.

---

## Option A — Recommended: Vercel (UI) + Railway/Render (API)

### Step 1 — Deploy backend (Railway or Render)

1. Push the `medical-rag-system` folder to GitHub.
2. Create a new **Railway** or **Render** web service from the repo root.
3. Set environment variables:

   | Variable | Value |
   |----------|-------|
   | `OPENROUTER_API_KEY` | Your key from https://openrouter.ai/keys |
   | `DISABLE_AUTH` | `1` |
   | `LLM_PROVIDER` | `openrouter` |
   | `EMBEDDING_PROVIDER` | `local` |

4. Use the included `Dockerfile` (Render/Railway detect it automatically).
5. On first deploy, the container builds the knowledge base if missing (or run `python scripts/build_kb.py` in a one-off job).
6. Copy your public API URL, e.g. `https://medical-rag-api.up.railway.app`.

### Step 2 — Deploy frontend on Vercel

1. Go to https://vercel.com → **Add New Project** → import your GitHub repo.
2. **Root Directory:** leave as repo root (`medical-rag-system` if the repo is only this folder).
3. Vercel reads `vercel.json` automatically:
   - Install: `npm install --prefix frontend`
   - Build: `npm run build --prefix frontend`
   - Output: `frontend/dist`
4. Add environment variable in Vercel:

   | Variable | Value |
   |----------|-------|
   | `VITE_API_URL` | `https://your-backend-url.railway.app` (no trailing slash) |

5. Deploy. Open your `*.vercel.app` URL.

### Step 3 — CORS (if needed)

FastAPI already allows browser requests in dev. If the UI cannot reach the API, add your Vercel domain to CORS in `app.py`.

---

## Option B — Single server (no Vercel)

Build the frontend and serve everything from FastAPI:

```powershell
cd medical-rag-system
cd frontend && npm install && npm run build && cd ..
uvicorn app:api --host 0.0.0.0 --port 8000
```

Open http://localhost:8000 — no `VITE_API_URL` needed.

---

## Option C — Docker (VPS / cloud VM)

```powershell
cd medical-rag-system
copy .env.example .env
# Set OPENROUTER_API_KEY in .env
docker compose up --build
```

---

## Vercel project settings checklist

- [ ] Repo root contains `vercel.json`
- [ ] `VITE_API_URL` set to live backend URL
- [ ] Backend `/healthz` returns `llm_reachable: true`
- [ ] Do **not** upload `.env` with secrets to GitHub — use Vercel/Railway env vars

---

## Folder layout (what gets deployed where)

```
medical-rag-system/
├── frontend/          → Vercel (UI only)
├── app.py             → Railway/Render (API)
├── data/              → Railway/Render (knowledge base)
├── agents/            → Railway/Render
├── rag/               → Railway/Render
└── vercel.json        → Vercel build config
```

College PDFs, PPTs, and reports live in `../project-docs/` and are **not** deployed.
