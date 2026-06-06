from utils.llm_factory import get_llm
from utils.helpers import log_interaction
from utils.language import llm_language_instruction
import re


class SupervisorAgent:
    """
    Reviews Doctor agent's analysis, validates recommendations, and ensures compliance. Finalizes treatment plan.
    """
    def __init__(self, llm_model="meta-llama/llama-3.2-3b-instruct"):
        self.llm = get_llm(model=llm_model)
        self.role = "Medical Supervisor"
        self.tools = ["reviewer", "compliance_checker"]
    
    async def review(self, doctor_analysis):
        log_interaction(self.role, f"Reviewing: {doctor_analysis}")
        lang_instruction = llm_language_instruction(doctor_analysis.get("language", "en"))
        prompt = f"""
You are a senior medical supervisor for a medical information system.
Create a safe, general next-steps plan grounded in the doctor's analysis.
Include SPECIFIC protocol doses (mg/ml), frequency, and duration when recommending medicines from the doctor's analysis.
{lang_instruction}

You must start your response with 'Treatment Plan:' on a new line, followed by your plan, then 'Additional Tests:' on a new line, followed by a bulleted list. Do not include any other text, explanation, or section.

- In the 'Additional Tests' section, you must name each test specifically (e.g., 'HIV viral load', 'Complete Blood Count', 'Liver Function Test', etc.). Do not use generic placeholders like '[Test 1]'.
- In the 'Treatment Plan', when medicines are needed, state generic name with exact dose, frequency, and duration from the doctor's analysis/protocols.
- Respond ONLY with the required sections, no extra explanation or meta-comments.

Doctor's Analysis:
{doctor_analysis.get('analysis')}

Treatment Plan:
[Your plan here]

Additional Tests:
- [Test 1]
- [Test 2]
"""
        response = await self.llm.agenerate([prompt])
        text = response[0] if response else ""

        # Robust parsing using regex
        treatment_plan = ""
        additional_tests = []
        m_plan = re.search(r"Treatment Plan:\s*(.*?)(?:\nAdditional Tests:|$)", text, re.DOTALL | re.IGNORECASE)
        if m_plan:
            treatment_plan = m_plan.group(1).strip()
        m_tests = re.search(r"Additional Tests:\s*(.*)", text, re.DOTALL | re.IGNORECASE)
        if m_tests:
            additional_tests = [t.strip("- ").strip() for t in m_tests.group(1).strip().split("\n") if t.strip()]

        final_plan = {
            "treatment": treatment_plan,
            "additional_tests": additional_tests
        }
        result = {
            "status": "ok",
            "input_type": doctor_analysis.get("input_type"),
            "language": doctor_analysis.get("language", "en"),
            "final_plan": final_plan,
            "analysis": doctor_analysis.get("analysis"),
            "recommendations": doctor_analysis.get("recommendations"),
            "file_path": doctor_analysis.get("file_path"),
            "metadata": {
                "source": self.role
            }
        }
        log_interaction(self.role, "Finalized plan and compliance check.")
        return result 