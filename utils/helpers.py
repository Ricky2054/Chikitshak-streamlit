"""
Utility functions for logging, monitoring, and general helpers.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _log_dir() -> Path:
    root = Path(__file__).resolve().parents[1]
    log_path = root / "logs"
    log_path.mkdir(parents=True, exist_ok=True)
    return log_path


def log_interaction(agent, message):
    """Append a JSONL record. Logging failures must not crash the app."""
    record: dict[str, Any] = {
        "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "agent": agent,
        "message": message,
    }
    try:
        with (_log_dir() / "agent_interactions.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        return