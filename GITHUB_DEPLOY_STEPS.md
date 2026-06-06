# Push to GitHub & Deploy — Quick Steps

Your code is **committed locally** (`310dd6e`). Follow these steps on your machine.

---

## Part 1 — Push to GitHub

### Option A — Push to existing repo (Ricky2054)

You must be logged into GitHub as **Ricky2054** (or be added as collaborator).

```powershell
cd "c:\Users\HP\Downloads\final year\medical-rag-system"
git push -u origin main
```

If you get **403 Permission denied**, use a Personal Access Token:

1. GitHub → Settings → Developer settings → Personal access tokens
2. Create token with `repo` scope
3. Push again; use token as password when prompted

### Option B — New repo under your account

1. Create empty repo on GitHub: https://github.com/new  
   Name: `medical-rag-system`
2. Run:

```powershell
cd "c:\Users\HP\Downloads\final year\medical-rag-system"
git remote set-url origin https://github.com/YOUR_USERNAME/medical-rag-system.git
git push -u origin main
```

---

## Part 2 — Deploy backend (Render — recommended)

1. Go to https://render.com → **New +** → **Blueprint** (or Web Service)
2. Connect your GitHub repo
3. Render detects `render.yaml` and `Dockerfile`
4. Add environment variables:

| Variable | Value |
|----------|-------|
| `OPENROUTER_API_KEY` | Your key from https://openrouter.ai/keys |
| `DISABLE_AUTH` | `1` |
| `LLM_PROVIDER` | `openrouter` |
| `EMBEDDING_PROVIDER` | `local` |

5. Deploy → copy public URL, e.g. `https://medical-rag-api.onrender.com`
6. Wait for `/healthz` to return `kb_ready: true` (first deploy may take 5–10 min)

---

## Part 3 — Deploy frontend (Vercel)

1. Go to https://vercel.com → **Add New Project**
2. Import your GitHub repo
3. Vercel reads `vercel.json` automatically
4. Add environment variable:

| Variable | Value |
|----------|-------|
| `VITE_API_URL` | Your Render backend URL (no trailing slash) |

5. Click **Deploy**
6. Open your `*.vercel.app` URL

### Or deploy from CLI (your machine)

```powershell
cd "c:\Users\HP\Downloads\final year\medical-rag-system"
vercel login
vercel --prod
```

Then set `VITE_API_URL` in Vercel dashboard → Project → Settings → Environment Variables → Redeploy.

---

## Part 4 — Verify

```powershell
# Backend
Invoke-RestMethod https://YOUR-BACKEND-URL/healthz

# Frontend — open in browser and run a symptoms test query
```

---

## Important

- **Never commit `.env`** — only `.env.example` is in the repo
- **Do not** put `OPENROUTER_API_KEY` in Vercel (backend only)
- Frontend on Vercel + Backend on Render is the correct split
