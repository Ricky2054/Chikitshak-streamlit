import streamlit as st
import os
from datetime import datetime
import asyncio
import re
from agents.gatekeeper import GatekeeperAgent
from agents.doctor import DoctorAgent
from agents.supervisor import SupervisorAgent
from rag.embeddings import get_embedder
from rag.knowledge_base import create_medical_knowledge_base

st.set_page_config(page_title="Medical AI Assistant", layout="wide")
st.title("Medical AI Assistant")

# Helper to format LLM output for user-friendly display
def format_llm_output(text):
    summary = ""
    recommendations = []
    warnings = []
    lines = text.split('\n')
    for line in lines:
        if re.search(r'(recommend|suggest|should|advise)', line, re.I):
            recommendations.append(line.strip())
        elif re.search(r'(warning|caution|danger|side effect)', line, re.I):
            warnings.append(line.strip())
        elif not summary and line.strip():
            summary = line.strip()
    return summary, recommendations, warnings

# Sidebar: ONLY instructions/info, NO outputs/results
with st.sidebar:
    st.header("How to Use")
    st.markdown("""
    1. **Upload your medical documents** (PDF, image, or text) in the section below.
    2. Click **Refresh Knowledge Base** after uploading.
    3. Enter your symptoms, prescription, or test results in the main form.
    4. (Optional) Upload a file with your input.
    5. Click **Submit** to get an AI-powered medical analysis and recommendations.
    """)
    st.info("All processing is local and private. No data leaves your computer.")

# Helper to save uploaded file
def save_uploaded_file(uploaded_file, input_type):
    if uploaded_file is None:
        return None
    folder_map = {
        "Prescription Review": "data/drug_interactions/",
        "Test Results": "data/test_references/",
        "Symptoms": "data/medical_protocols/"
    }
    folder = folder_map.get(input_type, "data/medical_protocols/")
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{uploaded_file.name}"
    file_path = os.path.join(folder, filename)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# Knowledge base and agents (init only once)
if 'embedder' not in st.session_state:
    st.session_state['embedder'] = get_embedder()
if 'knowledge_base' not in st.session_state:
    st.session_state['knowledge_base'] = None
if 'gatekeeper' not in st.session_state:
    st.session_state['gatekeeper'] = GatekeeperAgent()
if 'doctor' not in st.session_state:
    st.session_state['doctor'] = DoctorAgent()
if 'supervisor' not in st.session_state:
    st.session_state['supervisor'] = SupervisorAgent()

gatekeeper = st.session_state['gatekeeper']
doctor = st.session_state['doctor']
supervisor = st.session_state['supervisor']
embedder = st.session_state['embedder']

# Document upload and knowledge base refresh UI (main area only)
st.subheader("Step 1: Upload Medical Documents")
doc_input_type = st.selectbox("Document Type", ["Symptoms", "Prescription Review", "Test Results"], key="doc_type", help="What kind of document are you uploading?")
doc_uploaded_file = st.file_uploader("Upload a document (PDF, image, or text)", type=["pdf", "jpg", "png", "jpeg", "txt"], key="doc_upload", help="Upload your medical files here.")
if st.button("Add Document to Knowledge Base"):
    if doc_uploaded_file is not None:
        save_uploaded_file(doc_uploaded_file, doc_input_type)
        st.success(f"Document '{doc_uploaded_file.name}' uploaded and saved.")
    else:
        st.warning("Please upload a document before adding.")
if st.button("Step 2: Refresh Knowledge Base"):
    st.session_state['knowledge_base'] = create_medical_knowledge_base(embedder)
    if st.session_state['knowledge_base'] is not None:
        st.success("Knowledge base refreshed with current documents.")
    else:
        st.error("No valid documents found. Please upload documents first.")

knowledge_base = st.session_state['knowledge_base']

# Async workflow for agent chain
async def agent_workflow(user_input, input_type, uploaded_file, knowledge_base):
    agent_log = []
    file_path = None
    if uploaded_file is not None:
        file_path = save_uploaded_file(uploaded_file, input_type)
        agent_log.append(f"File saved to: {file_path}")
    gatekeeper_result = await gatekeeper.process(user_input, input_type, file_path)
    agent_log.append({"Gatekeeper": gatekeeper_result})
    if gatekeeper_result.get("status") != "ok":
        return agent_log, gatekeeper_result
    doctor_result = await doctor.analyze(gatekeeper_result, knowledge_base)
    agent_log.append({"Doctor": doctor_result})
    if doctor_result.get("status") != "ok":
        return agent_log, doctor_result
    supervisor_result = await supervisor.review(doctor_result)
    agent_log.append({"Supervisor": supervisor_result})
    return agent_log, supervisor_result

# Main UI (all outputs/results here)
st.subheader("Step 3: Get Your Medical Analysis")
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("**Describe your case below.**")
    input_type = st.selectbox("Type of Input", ["Symptoms", "Prescription Review", "Test Results"], help="What are you submitting?")
    user_input = st.text_area("Describe your input:", help="Type your symptoms, prescription, or test results here.")
    uploaded_file = st.file_uploader("(Optional) Upload a file with your input", type=["pdf", "jpg", "png"], key="main_upload", help="Attach a file if you have one.")
    if st.button("Step 4: Submit for Analysis"):
        st.session_state['last_input'] = user_input
        st.session_state['last_type'] = input_type
        st.session_state['last_file'] = uploaded_file
        st.session_state['agent_log'] = []
        if knowledge_base is None:
            st.error("Knowledge base is empty. Please upload and refresh documents first.")
        else:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            agent_log, final_result = loop.run_until_complete(agent_workflow(user_input, input_type, uploaded_file, knowledge_base))
            st.session_state['agent_log'] = agent_log
            st.session_state['final_result'] = final_result

# Move output sections below the columns for full width
def show_agent_outputs():
    st.header("Agent Reasoning (Step-by-Step)")
    if 'agent_log' in st.session_state:
        for entry in st.session_state['agent_log']:
            if isinstance(entry, dict):
                for agent, output in entry.items():
                    with st.expander(f"{agent} Output", expanded=(agent == 'Supervisor')):
                        if isinstance(output, dict):
                            # DoctorAgent: pretty print LLM output
                            if agent == "Doctor" and output.get("analysis"):
                                summary, recs, warns = format_llm_output(output["analysis"])
                                if summary:
                                    st.markdown(f"**Summary:** {summary}")
                                if recs:
                                    st.markdown("**Recommendations:**")
                                    for r in recs:
                                        st.markdown(f"- {r}")
                                if warns:
                                    st.markdown("**Warnings:**")
                                    for w in warns:
                                        st.markdown(f":warning: {w}")
                            # SupervisorAgent: show final plan in plain language
                            elif agent == "Supervisor" and output.get("final_plan"):
                                plan = output["final_plan"]
                                if plan and plan.get('treatment', '').strip():
                                    st.success(f"**Treatment Plan:** {plan.get('treatment', '')}")
                                    if plan.get('additional_tests'):
                                        st.info(f"**Additional Tests:** {', '.join(plan['additional_tests'])}")
                                else:
                                    # Fallback: show raw LLM output for debugging
                                    raw = output.get('analysis', '')
                                    if raw:
                                        st.warning("Raw Supervisor LLM Output (for debugging):")
                                        st.code(raw)
                            # Gatekeeper: show sanitized input
                            elif agent == "Gatekeeper" and output.get("sanitized_input"):
                                st.markdown(f"**Sanitized Input:** {output['sanitized_input']}")
                            # Show relevant docs if present
                            if output.get("relevant_docs"):
                                with st.expander("Relevant Documents Used"):
                                    for i, doc in enumerate(output["relevant_docs"]):
                                        st.markdown(f"**Doc {i+1}:** {doc[:400]}{'...' if len(doc) > 400 else ''}")
                        else:
                            st.write(output)
            else:
                # entry is not a dict (e.g., a string like 'File saved to: ...')
                st.info(str(entry))
    st.header("Final Medical Recommendation")
    if 'final_result' in st.session_state:
        if isinstance(st.session_state['final_result'], dict):
            if st.session_state['final_result'].get("status") == "ok":
                plan = st.session_state['final_result'].get("final_plan")
                if plan:
                    st.success(f"**Treatment Plan:** {plan.get('treatment', '')}")
                    if plan.get('additional_tests'):
                        st.info(f"**Additional Tests:** {', '.join(plan['additional_tests'])}")
                else:
                    # If no plan, show formatted analysis
                    analysis = st.session_state['final_result'].get("analysis")
                    if analysis:
                        summary, recs, warns = format_llm_output(analysis)
                        if summary:
                            st.markdown(f"**Summary:** {summary}")
                        if recs:
                            st.markdown("**Recommendations:**")
                            for r in recs:
                                st.markdown(f"- {r}")
                        if warns:
                            st.markdown("**Warnings:**")
                            for w in warns:
                                st.markdown(f":warning: {w}")
                    else:
                        st.success("See above for details.")
            else:
                st.error(st.session_state['final_result'].get("message", "An error occurred."))

# Show outputs below the columns
show_agent_outputs() 