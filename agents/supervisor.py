from utils.ollama_client import OllamaLLM
from langchain.memory import ConversationBufferMemory
from utils.helpers import log_interaction
import re

class SupervisorAgent:
    """
    Reviews Doctor agent's analysis, validates recommendations, and ensures compliance. Finalizes treatment plan.
    """
    def __init__(self, llm_model="llama3.2:1b"):
        self.llm = OllamaLLM(model=llm_model)
        self.role = "Medical Supervisor"
        self.tools = ["reviewer", "compliance_checker"]
        self.memory = ConversationBufferMemory()
    
    async def review(self, doctor_analysis):
        log_interaction(self.role, f"Reviewing: {doctor_analysis}")
        prompt = f"""
You are a senior medical supervisor. Given the following doctor's analysis, synthesize a final treatment plan and list any additional tests needed.

You must start your response with 'Treatment Plan:' on a new line, followed by your plan, then 'Additional Tests:' on a new line, followed by a bulleted list. Do not include any other text, explanation, or section.

- In the 'Additional Tests' section, you must name each test specifically (e.g., 'HIV viral load', 'Complete Blood Count', 'Liver Function Test', etc.). Do not use generic placeholders like '[Test 1]'.
- In the 'Treatment Plan', if you recommend any medicine, you must specify the medicine name and dosage (e.g., 'Tenofovir 300mg once daily').
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
        text = response[0]

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