from utils.ollama_client import OllamaLLM
from langchain.memory import ConversationBufferMemory
from utils.helpers import log_interaction
import asyncio

class DoctorAgent:
    """
    Analyzes symptoms, reviews prescriptions, and provides initial recommendations. Integrates RAG for knowledge retrieval.
    """
    def __init__(self, llm_model="deepseek-r1:1.5b"):
        self.llm = OllamaLLM(model=llm_model)
        self.role = "Medical Doctor"
        self.tools = ["symptom_analyzer", "prescription_reviewer", "rag_retriever"]
        self.memory = ConversationBufferMemory()
    
    async def analyze(self, gatekeeper_result, knowledge_base=None):
        log_interaction(self.role, f"Analyzing: {gatekeeper_result}")
        relevant_docs = []
        context = ""
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
            context = "\n\n".join(
                f"Doc {i+1}: {doc.page_content[:500]}" for i, doc in enumerate(relevant_docs)
            )
        else:
            context = "No relevant documents found."

        prompt = f"""
        You are an experienced medical doctor. Based on the following patient input and relevant medical documents, provide a detailed, realistic, and actionable response.

        Patient Input:
        {gatekeeper_result.get('sanitized_input')}

        Relevant Medical Documents:
        {context}

        Your response must include:

        Summary (2-3 sentences):  
        - Briefly summarize the patient's case and main concerns.

        Recommendations (3-5 bullet points):  
        - For each recommendation, include specific medicine names (if appropriate), recommended dosages, and duration of treatment, just as a real doctor would.  
        - If lab tests or follow-up are needed, specify which ones and when.  
        - Be as specific and practical as possible.

        Warnings (bullet points):  
        - List any important warnings, side effects, or red flags for the patient to watch for.

        **Important:**  
        - Do NOT explain your reasoning or say what you are about to do.  
        - Do NOT include any meta-comments or "<think>" sections.  
        - Only output the sections above, with real medical details.

        Respond in this format:

        Summary:
        [Your summary here]

        Recommendations:
        - [Medicine name, dosage, frequency, duration, and any other instructions]
        - [Next recommendation]
        - [Next recommendation]

        Warnings:
        - [Warning or red flag 1]
        - [Warning or red flag 2]
        """
        response = await self.llm.agenerate([prompt])
        result = {
            "status": "ok",
            "input_type": gatekeeper_result.get("input_type"),
            "analysis": response[0],
            "recommendations": [],  # Optionally parse recommendations from response
            "relevant_docs": [doc.page_content for doc in relevant_docs],
            "file_path": gatekeeper_result.get("file_path"),
            "metadata": {"source": self.role}
        }
        log_interaction(self.role, "Generated analysis and recommendations.")
        return result 