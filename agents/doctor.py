from utils.llm_factory import get_llm
from utils.helpers import log_interaction
from utils.language import llm_language_instruction
import asyncio
import re


def _normalize_headers(text: str) -> str:
    t = (text or "").strip()
    for name in ("Summary", "Guidance", "Red Flags", "Sources"):
        t = re.sub(rf"(?m)^\s*#+\s*{name}\s*:?\s*$", f"{name}:", t, flags=re.IGNORECASE)
        t = re.sub(rf"\*\*{name}\*\*\s*:?", f"{name}:", t, flags=re.IGNORECASE)
        t = re.sub(rf"(?m)^\s*{name}\s*-\s*", f"{name}:\n", t, flags=re.IGNORECASE)
    return t.strip()


def _response_score(text: str) -> int:
    t = _normalize_headers(text)
    if len(t) < 80:
        return 0
    score = min(len(t) // 80, 8)
    for section in ("Summary:", "Guidance:", "Red Flags:", "Sources:"):
        if section.lower() in t.lower():
            score += 3
    m = re.search(r"Guidance:\s*(.+?)(?=\n\s*Red Flags:|\n\s*Sources:|\Z)", t, re.DOTALL | re.IGNORECASE)
    if m:
        score += len(re.findall(r"^\s*[-•*]\s+", m.group(1), re.MULTILINE)) * 2
    return score


def _response_complete(text: str) -> bool:
    return _response_score(text) >= 14

class DoctorAgent:
    """
    Analyzes symptoms, reviews prescriptions, and provides initial recommendations. Integrates RAG for knowledge retrieval.
    """
    def __init__(self, llm_model="meta-llama/llama-3.2-3b-instruct"):
        self.llm = get_llm(model=llm_model)
        self.role = "Medical Doctor"
        self.tools = ["symptom_analyzer", "prescription_reviewer", "rag_retriever"]
    
    async def analyze(self, gatekeeper_result, knowledge_base=None):
        log_interaction(self.role, f"Analyzing: {gatekeeper_result}")
        relevant_docs = []
        context = ""
        sources = []
        if knowledge_base and gatekeeper_result.get("sanitized_input"):
            retriever = knowledge_base.as_retriever(search_kwargs={"k": 5})
            try:
                relevant_docs = await retriever.ainvoke(gatekeeper_result["sanitized_input"])
            except (AttributeError, NotImplementedError):
                loop = asyncio.get_event_loop()
                relevant_docs = await loop.run_in_executor(
                    None, lambda: retriever.invoke(gatekeeper_result["sanitized_input"])
                )
            # Summarize the context for the LLM
            context_parts = []
            for i, doc in enumerate(relevant_docs):
                meta = getattr(doc, "metadata", {}) or {}
                source = meta.get("source", "")
                page = meta.get("page")
                sources.append({"source": source, "page": page})
                context_parts.append(
                    f"Doc {i+1} (source={source}, page={page}):\n{(doc.page_content or '')[:800]}"
                )
            context = "\n\n".join(context_parts)
        else:
            context = "No relevant documents found."

        lang_instruction = llm_language_instruction(gatekeeper_result.get("language", "en"))
        patient_ctx = gatekeeper_result.get("patient_context", "Patient details not provided.")
        input_type = gatekeeper_result.get("input_type", "")
        type_section = ""
        if input_type == "Prescription Review":
            type_section = """
        Prescription-specific requirements:
        - List EVERY medication with generic name, strength, frequency, and duration.
        - Note interactions, duplications, contraindications, and protocol alignment.
        - Adjust recommendations for patient age, weight, and gender when provided.
        """
        elif input_type == "Test Results":
            type_section = """
        Test-results-specific requirements:
        - Interpret the lab values in clinical context.
        - Guidance MUST include at least 4 bullet points: likely causes, follow-up tests, monitoring steps, and when to seek urgent care.
        - In Medications, list protocol first-line drugs with SPECIFIC doses if treatment is indicated.
        """
        elif input_type == "Symptoms":
            type_section = """
        Symptoms-specific requirements:
        - Guidance MUST include at least 4 bullet points covering self-care, clinical workup, follow-up, and monitoring.
        - Red Flags MUST list at least 2 urgent warning signs.
        - In Medications, list first-line protocol drugs with SPECIFIC dose, frequency, and duration from documents.
        """

        dose_section = """
        Medications (required — list each drug with SPECIFIC dosing from protocols):
        - [Generic name]: [strength] [frequency] [duration if applicable]
        Example: Azithromycin: 500 mg once daily for 3 days
        Use patient age/weight to adjust doses when documents specify pediatric or weight-based regimens.
        If no medication is indicated, write: None indicated from protocols.
        """

        prompt = f"""
        You are a clinical decision-support assistant grounded in the provided medical documents.
        ALWAYS include specific protocol doses (mg/ml), frequency (OD/BD/TDS), and duration (days) from the knowledge base.
        {lang_instruction}

        Patient Details:
        {patient_ctx}

        Patient Input:
        {gatekeeper_result.get('sanitized_input')}

        Relevant Medical Documents:
        {context}

        Your response MUST include ALL sections below. Never skip Guidance.

        Summary (2-3 sentences):
        - Briefly summarize the case and main concerns.

        Guidance (minimum 4 bullet points, each starting with "-"):
        - Actionable clinical recommendations from protocols.
        - Follow-up tests or monitoring.
        - Self-care or supportive measures where appropriate.

        Red Flags (bullet points):
        - Warning signs requiring urgent medical evaluation.

        Sources (bullet points):
        - Document sources used (file name + page if available).

        {dose_section}
        {type_section}

        Rules:
        - Do NOT include meta-commentary or reasoning about what you will do.
        - Only output the sections above with real clinical detail.

        Format:

        Summary:
        [text]

        Guidance:
        - [point]
        - [point]
        - [point]
        - [point]

        Red Flags:
        - [flag]

        Sources:
        - [source]

        Medications:
        - [Generic name]: [specific dose and frequency]
        """
        response = await self.llm.agenerate([prompt])
        raw = _normalize_headers(response[0] if response else "")
        if not _response_complete(raw):
            retry_prompt = f"""
Respond ONLY in this exact structure. No intro text.

Summary:
[2-3 sentences about the case]

Guidance:
- [recommendation 1]
- [recommendation 2]
- [recommendation 3]
- [recommendation 4]

Red Flags:
- [urgent sign 1]
- [urgent sign 2]

Sources:
- [source from documents]

Medications:
- [Generic name]: [specific mg/ml dose, frequency, duration]

Case type: {input_type}
Patient: {patient_ctx}
Input: {gatekeeper_result.get('sanitized_input')}
Documents: {context[:2000]}
{lang_instruction}
"""
            retry_resp = await self.llm.agenerate([retry_prompt])
            retry_raw = _normalize_headers(retry_resp[0] if retry_resp else "")
            if _response_score(retry_raw) > _response_score(raw):
                raw = retry_raw
        cleaned = raw
        result = {
            "status": "ok",
            "input_type": gatekeeper_result.get("input_type"),
            "language": gatekeeper_result.get("language", "en"),
            "analysis": cleaned,
            "recommendations": [],  # Optionally parse recommendations from response
            "relevant_docs": [doc.page_content for doc in relevant_docs],
            "sources": sources,
            "file_path": gatekeeper_result.get("file_path"),
            "metadata": {"source": self.role}
        }
        log_interaction(self.role, "Generated analysis and recommendations.")
        return result 