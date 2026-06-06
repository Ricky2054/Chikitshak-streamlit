from utils.helpers import log_interaction
from utils.validators import validate_input
from utils.language import blocked_message, normalize_language
import re


_PII_PATTERNS = [
    (re.compile(r"\b\d{10}\b"), "[REDACTED_PHONE]"),
    (re.compile(r"\b\d{12}\b"), "[REDACTED_ID]"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[REDACTED_EMAIL]"),
]

_PRESCRIBING_PATTERNS = [
    re.compile(r"\bprescribe\s+me\b", re.I),
    re.compile(r"\bprescribe\s+(an?\s+)?(antibiotic|medicine|medication|drug|tablet|pill)s?\b", re.I),
    re.compile(r"\bwrite\s+me\s+a\s+prescription\b", re.I),
    re.compile(r"\bgive\s+me\s+(an?\s+)?(antibiotic|medicine|medication|prescription|drug)s?\b", re.I),
    re.compile(r"\bcan\s+you\s+prescribe\b", re.I),
    re.compile(r"\bplease\s+prescribe\b", re.I),
    re.compile(r"\bneed\s+(you\s+to\s+)?prescribe\b", re.I),
    re.compile(r"\bi\s+need\s+(an?\s+)?(antibiotic|prescription|medicine)s?\b", re.I),
    re.compile(r"\bstart\s+me\s+on\s+(an?\s+)?(antibiotic|medicine|medication)s?\b", re.I),
    re.compile(r"\bget\s+me\s+(an?\s+)?(antibiotic|prescription|medicine)s?\b", re.I),
]

_DOSE_PATTERNS = [
    re.compile(r"\bwhat\s+(exact\s+)?dose\b", re.I),
    re.compile(r"\bhow\s+much\s+should\s+i\s+take\b", re.I),
    re.compile(r"\bhow\s+many\s+(tablets?|pills?|capsules?)\b", re.I),
    re.compile(r"\bdosage\s+should\s+i\b", re.I),
    re.compile(r"\bwhat\s+medicine\s+should\s+i\s+take\b", re.I),
    re.compile(r"\bwhich\s+(antibiotic|medicine|medication)\s+should\s+i\b", re.I),
    re.compile(r"\bwhat\s+(antibiotic|medicine|medication)\s+should\s+i\s+take\b", re.I),
]


def _redact_pii(text: str) -> str:
    redacted = text
    for pat, repl in _PII_PATTERNS:
        redacted = pat.sub(repl, redacted)
    return redacted


def _looks_like_rx_review(text: str) -> bool:
    t = text.lower()
    rx_markers = ["tab.", "cap.", "syr.", "inj.", " mg ", " bd", " od ", " tds", "review", "interaction", "prescription"]
    return sum(1 for m in rx_markers if m in t) >= 2


def _is_medication_or_dose_request(text: str, input_type: str = "") -> bool:
    t = f" {text.lower().strip()} "

    for pat in _PRESCRIBING_PATTERNS:
        if pat.search(t):
            return True

    if "prescribe" in t and any(w in t for w in [" me ", " my ", "for me", "right now", " for my "]):
        return True

    for pat in _DOSE_PATTERNS:
        if pat.search(t):
            return True

    intent_terms = ["dose", "dosage", "how much should i take", "how many tablets", "how many pills"]
    if any(term in t for term in intent_terms) and ("?" in t or "should i" in t):
        return True

    antibiotic_asks = ["recommend antibiotic", "suggest antibiotic", "which antibiotic", "what antibiotic"]
    if any(p in t for p in antibiotic_asks):
        if input_type == "Prescription Review" and _looks_like_rx_review(text):
            return False
        if "review" not in t and not _looks_like_rx_review(text):
            return True

    return False


class GatekeeperAgent:
    """
    First point of contact: validates, sanitizes, and routes medical data.
    """

    def __init__(self):
        self.role = "Medical Gatekeeper"
        self.tools = ["input_validator", "data_sanitizer", "router"]

    async def process(self, user_input, input_type, file_path=None, language="en", patient_context=""):
        log_interaction(self.role, f"Received input: {user_input}")
        lang = normalize_language(language)
        valid = validate_input(user_input, input_type)
        if not valid:
            return {"status": "error", "message": "Invalid input", "input_type": input_type}
        sanitized_input = _redact_pii(str(user_input).strip())

        if _is_medication_or_dose_request(sanitized_input, input_type):
            return {
                "status": "blocked",
                "message": blocked_message(lang),
                "input_type": input_type,
                "language": lang,
                "sanitized_input": sanitized_input,
                "file_path": file_path,
                "metadata": {"source": self.role},
            }

        result = {
            "status": "ok",
            "input_type": input_type,
            "language": lang,
            "sanitized_input": sanitized_input,
            "file_path": file_path,
            "patient_context": patient_context,
            "metadata": {"source": self.role},
        }
        log_interaction(self.role, f"Validated and sanitized input: {sanitized_input}")
        return result
