"""rag.knowledge_base

Build and maintain a local persistent FAISS knowledge base for the Medical RAG System.

Notes:
- Supports PDF + plain text + Markdown.
- Persists a FAISS index to disk for fast startup.
- Maintains a simple manifest of file stats to trigger rebuilds when sources change.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

try:
    from langchain_core.documents import Document
except Exception:  # pragma: no cover
    from langchain.schema import Document  # type: ignore

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except Exception:  # pragma: no cover
    from langchain.text_splitter import RecursiveCharacterTextSplitter  # type: ignore
from langchain_community.vectorstores import FAISS

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None


SUPPORTED_EXTS = {".pdf", ".txt", ".md"}


@dataclass(frozen=True)
class KnowledgeBaseConfig:
    paths: List[str]
    persist_dir: str
    manifest_name: str = "manifest.json"
    chunk_size: int = 1000
    chunk_overlap: int = 200


def _project_root() -> Path:
    # medical_rag_system/
    return Path(__file__).resolve().parents[1]


def _normalize_paths(paths: Optional[List[str]]) -> List[Path]:
    base = _project_root()
    out: List[Path] = []
    for p in (paths or []):
        candidate = Path(p)
        if not candidate.is_absolute():
            candidate = (base / candidate).resolve()
        out.append(candidate)
    return out


def _iter_files(kb_paths: List[Path]) -> Iterable[Path]:
    for p in kb_paths:
        if not p.exists():
            continue
        if p.is_file():
            if p.suffix.lower() in SUPPORTED_EXTS:
                yield p
            continue
        for f in p.glob("**/*"):
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS:
                yield f


def _file_record(path: Path) -> dict:
    stat = path.stat()
    return {"path": str(path), "size": stat.st_size, "mtime": int(stat.st_mtime)}


def _compute_manifest(kb_paths: List[Path]) -> dict:
    files = sorted({str(p): p for p in _iter_files(kb_paths)}.values(), key=lambda x: str(x))
    return {"version": 1, "files": [_file_record(f) for f in files]}


def _load_manifest(manifest_path: Path) -> Optional[dict]:
    if not manifest_path.exists():
        return None
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _manifest_equal(a: Optional[dict], b: dict) -> bool:
    if not a:
        return False
    return a.get("version") == b.get("version") and a.get("files") == b.get("files")


def _load_pdf_documents(file_path: Path) -> List[Document]:
    if PdfReader is None:
        raise RuntimeError("pypdf is not installed; cannot parse PDFs")
    reader = PdfReader(str(file_path))
    docs: List[Document] = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            docs.append(
                Document(
                    page_content=text,
                    metadata={"source": str(file_path), "page": i + 1, "type": "pdf"},
                )
            )
    return docs


def _load_text_documents(file_path: Path) -> List[Document]:
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    if not text.strip():
        return []
    return [Document(page_content=text, metadata={"source": str(file_path), "type": "text"})]


def load_medical_documents(paths: Optional[List[str]] = None) -> List[Document]:
    default_paths = ["data/medical_protocols", "data/drug_interactions", "data/test_references"]
    kb_paths = _normalize_paths(paths or default_paths)
    docs: List[Document] = []
    for file_path in _iter_files(kb_paths):
        ext = file_path.suffix.lower()
        try:
            if ext == ".pdf":
                docs.extend(_load_pdf_documents(file_path))
            elif ext in {".txt", ".md"}:
                docs.extend(_load_text_documents(file_path))
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    return docs


def _split_documents(documents: List[Document], chunk_size: int, chunk_overlap: int) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_documents(documents)


def create_medical_knowledge_base(embedder, config: Optional[dict] = None):
    kb_cfg = (config or {}).get("knowledge_base", {}) or {}
    cfg = KnowledgeBaseConfig(
        paths=kb_cfg.get(
            "paths",
            ["data/medical_protocols", "data/drug_interactions", "data/test_references"],
        ),
        persist_dir=kb_cfg.get("persist_dir", ".cache/vectorstore"),
        chunk_size=int(kb_cfg.get("chunk_size", 1000)),
        chunk_overlap=int(kb_cfg.get("chunk_overlap", 200)),
    )

    base = _project_root()
    persist_dir = (base / cfg.persist_dir).resolve()
    persist_dir.mkdir(parents=True, exist_ok=True)
    index_dir = persist_dir / "faiss"
    manifest_path = persist_dir / cfg.manifest_name

    kb_paths = _normalize_paths(cfg.paths)
    current_manifest = _compute_manifest(kb_paths)
    saved_manifest = _load_manifest(manifest_path)

    if index_dir.exists() and _manifest_equal(saved_manifest, current_manifest):
        try:
            return FAISS.load_local(str(index_dir), embedder, allow_dangerous_deserialization=True)
        except Exception as e:
            print(f"Failed to load persisted FAISS index; rebuilding. Reason: {e}")

    documents = load_medical_documents(cfg.paths)
    if not documents:
        print("No documents found for knowledge base. Please add files to the configured paths.")
        return None
    chunks = _split_documents(documents, cfg.chunk_size, cfg.chunk_overlap)
    if not chunks:
        print("No text chunks could be created from the documents. Please check your files.")
        return None

    vectorstore = FAISS.from_documents(chunks, embedder)
    vectorstore.save_local(str(index_dir))
    manifest_path.write_text(json.dumps(current_manifest, indent=2), encoding="utf-8")
    return vectorstore


def index_file_into_knowledge_base(vectorstore, embedder, file_path: str, config: Optional[dict] = None):
    if vectorstore is None:
        return create_medical_knowledge_base(embedder, config=config)

    kb_cfg = (config or {}).get("knowledge_base", {}) or {}
    chunk_size = int(kb_cfg.get("chunk_size", 1000))
    chunk_overlap = int(kb_cfg.get("chunk_overlap", 200))
    persist_dir_cfg = kb_cfg.get("persist_dir", ".cache/vectorstore")

    base = _project_root()
    persist_dir = (base / persist_dir_cfg).resolve()
    persist_dir.mkdir(parents=True, exist_ok=True)
    index_dir = persist_dir / "faiss"
    manifest_path = persist_dir / "manifest.json"

    p = Path(file_path)
    if not p.is_absolute():
        p = (base / p).resolve()
    if not p.exists():
        return vectorstore

    docs: List[Document] = []
    ext = p.suffix.lower()
    if ext == ".pdf":
        docs = _load_pdf_documents(p)
    elif ext in {".txt", ".md"}:
        docs = _load_text_documents(p)
    if not docs:
        return vectorstore

    chunks = _split_documents(docs, chunk_size, chunk_overlap)
    if chunks:
        vectorstore.add_documents(chunks)
        vectorstore.save_local(str(index_dir))

    # Recompute manifest (simple + robust)
    configured_paths = kb_cfg.get(
        "paths",
        ["data/medical_protocols", "data/drug_interactions", "data/test_references"],
    )
    kb_paths = _normalize_paths(configured_paths)
    current_manifest = _compute_manifest(kb_paths)
    manifest_path.write_text(json.dumps(current_manifest, indent=2), encoding="utf-8")
    return vectorstore