import os
from datetime import datetime
import asyncio
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from agents.gatekeeper import GatekeeperAgent
from agents.doctor import DoctorAgent
from agents.supervisor import SupervisorAgent
from rag.embeddings import get_embedder
from rag.knowledge_base import create_medical_knowledge_base, index_file_into_knowledge_base
from utils.medication_enrichment import enrich_medications
from utils.patient_context import build_patient_context, patient_dict
from fastapi import FastAPI, HTTPException, Header, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import yaml

try:
    import firebase_admin
    from firebase_admin import credentials, auth as firebase_auth, firestore
except Exception:  # pragma: no cover
    firebase_admin = None
    credentials = None
    firebase_auth = None
    firestore = None

PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

api = FastAPI(title="Medical RAG System", version="1.0.0")
app = api


def load_config():
    cfg_path = os.getenv("MEDRAG_CONFIG", str(PROJECT_ROOT / "config.yaml"))
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


CONFIG = load_config()
DISABLE_AUTH = str(os.getenv("DISABLE_AUTH", "")).strip().lower() in {"1", "true", "yes"} or bool(
    (CONFIG.get("security", {}) or {}).get("disable_auth", False)
)

api.add_middleware(
    CORSMiddleware,
    allow_origins=(CONFIG.get("security", {}) or {}).get("allow_origins", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = None
if not DISABLE_AUTH and firebase_admin is not None:
    if not firebase_admin._apps:
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "firebase_service_account.json")
        if not os.path.exists(cred_path):
            raise RuntimeError(
                "Firebase service account JSON not found. Set GOOGLE_APPLICATION_CREDENTIALS or set DISABLE_AUTH=1."
            )
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    db = firestore.client()


class TokenRequest(BaseModel):
    id_token: str


class ProfileResponse(BaseModel):
    uid: str
    name: str
    email: str
    avatar: str


def verify_firebase_token(id_token: str):
    if DISABLE_AUTH:
        return "dev-user", {"uid": "dev-user", "name": "Dev", "email": "dev@example.com"}
    if firebase_auth is None:
        raise HTTPException(status_code=503, detail="Firebase auth is not available")
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        uid = decoded_token["uid"]
        return uid, decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


@api.post("/api/auth/verify", response_model=ProfileResponse)
def verify_auth_token(req: TokenRequest):
    uid, decoded = verify_firebase_token(req.id_token)
    name = decoded.get("name", "")
    email = decoded.get("email", "")
    avatar = decoded.get("picture", "")
    if db is not None:
        user_ref = db.collection("users").document(uid)
        user_ref.set(
            {
                "uid": uid,
                "name": name,
                "email": email,
                "avatar": avatar,
                "updated_at": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )
    return ProfileResponse(uid=uid, name=name, email=email, avatar=avatar)


@api.get("/api/profile", response_model=ProfileResponse)
def get_profile(authorization: str | None = Header(None)):
    if not DISABLE_AUTH:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing Bearer token")
        id_token = authorization.split(" ", 1)[1]
        uid, decoded = verify_firebase_token(id_token)
    else:
        uid, decoded = verify_firebase_token("")

    if db is None:
        return ProfileResponse(
            uid=uid,
            name=decoded.get("name", ""),
            email=decoded.get("email", ""),
            avatar=decoded.get("picture", ""),
        )
    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    user = user_doc.to_dict()
    return ProfileResponse(
        uid=uid,
        name=user.get("name", ""),
        email=user.get("email", ""),
        avatar=user.get("avatar", ""),
    )


embedder = None
knowledge_base = None
gatekeeper = None
doctor = None
supervisor = None
kb_lock = asyncio.Lock()
kb_build_task = None
kb_ready = False
kb_error = None


async def _build_kb_in_background():
    global knowledge_base, kb_ready, kb_error
    try:
        kb = await asyncio.to_thread(create_medical_knowledge_base, embedder, CONFIG)
        async with kb_lock:
            knowledge_base = kb
            kb_ready = kb is not None
            kb_error = None if kb is not None else "No documents indexed"
    except Exception as e:
        kb_error = str(e)
        print(f"Knowledge base build failed: {e}")


def _apply_provider_env():
    provider_cfg = CONFIG.get("provider", {}) or {}
    if not os.getenv("LLM_PROVIDER"):
        os.environ["LLM_PROVIDER"] = str(provider_cfg.get("llm", "openrouter"))
    if not os.getenv("EMBEDDING_PROVIDER"):
        os.environ["EMBEDDING_PROVIDER"] = str(provider_cfg.get("embeddings", "local"))


@api.on_event("startup")
async def _startup_init():
    global embedder, gatekeeper, doctor, supervisor, kb_build_task
    _apply_provider_env()
    models = CONFIG.get("models", {}) or {}
    embedder = get_embedder(models.get("embedder", "all-MiniLM-L6-v2"))
    gatekeeper = GatekeeperAgent()
    doctor = DoctorAgent(llm_model=models.get("doctor", "meta-llama/llama-3.2-3b-instruct"))
    supervisor = SupervisorAgent(llm_model=models.get("supervisor", "meta-llama/llama-3.2-3b-instruct"))
    kb_build_task = asyncio.create_task(_build_kb_in_background())


@api.get("/healthz")
async def healthz():
    llm_ok = False
    if doctor is not None and hasattr(doctor, "llm") and hasattr(doctor.llm, "ping"):
        try:
            llm_ok = await doctor.llm.ping()
        except Exception:
            llm_ok = False

    return {
        "status": "ok",
        "kb_ready": kb_ready,
        "kb_error": kb_error,
        "llm_reachable": llm_ok,
        "llm_provider": os.getenv("LLM_PROVIDER", "openrouter"),
        "embedding_provider": os.getenv("EMBEDDING_PROVIDER", "local"),
        "auth_disabled": DISABLE_AUTH,
    }


@api.post("/api/medical/analyze")
async def medical_analyze(
    user_input: str = Form(...),
    input_type: str = Form(...),
    language: str = Form("en"),
    patient_age: str = Form(""),
    patient_weight_kg: str = Form(""),
    patient_gender: str = Form("All"),
    file: UploadFile = File(None),
    authorization: str | None = Header(None),
):
    if not DISABLE_AUTH:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing Bearer token")
        id_token = authorization.split(" ", 1)[1]
        verify_firebase_token(id_token)

    file_path = None
    if file is not None:
        folder_map = {
            "Prescription Review": "data/drug_interactions/",
            "Test Results": "data/test_references/",
            "Symptoms": "data/medical_protocols/",
        }
        folder = folder_map.get(input_type, "data/medical_protocols/")
        os.makedirs(PROJECT_ROOT / folder, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = str(PROJECT_ROOT / folder / filename)
        with open(file_path, "wb") as f_out:
            f_out.write(await file.read())

    agent_log = []
    if file_path:
        agent_log.append(f"File saved to: {file_path}")

    if gatekeeper is None or doctor is None or supervisor is None:
        raise HTTPException(status_code=503, detail="Service not initialized yet")

    if hasattr(doctor, "llm") and hasattr(doctor.llm, "ping"):
        try:
            if not await doctor.llm.ping():
                raise HTTPException(
                    status_code=503,
                    detail="LLM provider is not reachable. Set OPENROUTER_API_KEY and verify your model names in config.yaml.",
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=503, detail="Unable to reach LLM provider.")

    patient_ctx = build_patient_context(patient_age, patient_weight_kg, patient_gender)
    gatekeeper_result = await gatekeeper.process(
        user_input, input_type, file_path, language=language, patient_context=patient_ctx
    )
    agent_log.append({"Gatekeeper": gatekeeper_result})
    if gatekeeper_result.get("status") != "ok":
        return JSONResponse({"agent_log": agent_log, "result": gatekeeper_result}, status_code=200)

    global knowledge_base
    if file_path and embedder is not None:
        async with kb_lock:
            knowledge_base = index_file_into_knowledge_base(knowledge_base, embedder, file_path, config=CONFIG)

    if knowledge_base is None:
        raise HTTPException(
            status_code=503,
            detail="Knowledge base is still building or empty. Check /healthz and server logs.",
        )

    doctor_result = await doctor.analyze(gatekeeper_result, knowledge_base)
    agent_log.append({"Doctor": doctor_result})
    if doctor_result.get("status") != "ok":
        return JSONResponse({"agent_log": agent_log, "result": doctor_result}, status_code=200)

    supervisor_result = await supervisor.review(doctor_result)
    agent_log.append({"Supervisor": supervisor_result})

    medications = await enrich_medications(
        supervisor_result.get("analysis", ""),
        doctor_result.get("relevant_docs", []),
        patient_dict(patient_age, patient_weight_kg, patient_gender),
    )
    supervisor_result["medications"] = medications
    supervisor_result["patient"] = patient_dict(patient_age, patient_weight_kg, patient_gender)

    return {"agent_log": agent_log, "result": supervisor_result}


if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        api.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @api.get("/")
    async def serve_frontend():
        return FileResponse(str(FRONTEND_DIST / "index.html"))

    @api.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path == "healthz":
            raise HTTPException(status_code=404, detail="Not found")
        candidate = FRONTEND_DIST / full_path
        if candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(FRONTEND_DIST / "index.html"))
