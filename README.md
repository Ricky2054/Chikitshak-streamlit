# Medical RAG System

A multi-agent Retrieval-Augmented Generation (RAG) system for medical workflows using Streamlit and OLLAMA local LLMs. Features Gatekeeper, Doctor, and Supervisor agents for collaborative medical data processing.

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Pull OLLAMA models:
   ```bash
   ollama pull llama3.2:1b
   ollama pull nomic-embed-text
   ollama pull deepseek-r1:1.5b
   ollama pull gemma3:1b
   ```
3. Run the app:
   ```bash
   streamlit run app.py
   ```

## Features
- Multi-agent medical workflow
- RAG with FAISS/ChromaDB
- Multimodal support (text, images, PDFs)
- Real-time agent communication
- Privacy and compliance 