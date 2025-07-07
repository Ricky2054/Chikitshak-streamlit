from utils.ollama_client import OllamaLLM
from utils.helpers import log_interaction
from utils.validators import validate_input

class GatekeeperAgent:
    """
    First point of contact: validates, sanitizes, and routes medical data. Maintains privacy compliance and logs all interactions.
    """
    def __init__(self, llm_model="llama3.2:1b"):
        self.llm = OllamaLLM(model=llm_model)
        self.role = "Medical Gatekeeper"
        self.tools = ["input_validator", "data_sanitizer", "router"]
    
    async def process(self, user_input, input_type, file_path=None):
        log_interaction(self.role, f"Received input: {user_input}")
        # Validate input
        valid = validate_input(user_input, input_type)
        if not valid:
            return {"status": "error", "message": "Invalid input", "input_type": input_type}
        # Sanitize input (stub)
        sanitized_input = user_input.strip()
        # Build structured output
        result = {
            "status": "ok",
            "input_type": input_type,
            "sanitized_input": sanitized_input,
            "file_path": file_path,
            "metadata": {
                "source": self.role
            }
        }
        log_interaction(self.role, f"Validated and sanitized input: {sanitized_input}")
        return result 