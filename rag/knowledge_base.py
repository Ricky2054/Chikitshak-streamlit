from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import os
from typing import List
from pathlib import Path
from PyPDF2 import PdfReader
from PIL import Image
import pytesseract
from langchain_community.vectorstores import FAISS

"""
Knowledge base creation and document processing for medical RAG system.
"""
def load_medical_documents():
    """
    Loads and parses all documents from data/medical_protocols, drug_interactions, and test_references.
    Supports PDF, image, and text files. Returns a list of langchain.schema.Document objects.
    """
    data_dirs = [
        "data/medical_protocols/",
        "data/drug_interactions/",
        "data/test_references/"
    ]
    documents: List[Document] = []
    for data_dir in data_dirs:
        for file_path in Path(data_dir).glob("**/*"):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                if ext == ".pdf":
                    # Parse PDF
                    try:
                        reader = PdfReader(str(file_path))
                        text = "\n".join(page.extract_text() or "" for page in reader.pages)
                        documents.append(Document(page_content=text, metadata={"source": str(file_path)}))
                    except Exception as e:
                        print(f"Error reading PDF {file_path}: {e}")
                elif ext in [".jpg", ".jpeg", ".png"]:
                    # Parse image with OCR
                    try:
                        image = Image.open(file_path)
                        text = pytesseract.image_to_string(image)
                        documents.append(Document(page_content=text, metadata={"source": str(file_path)}))
                    except Exception as e:
                        print(f"Error reading image {file_path}: {e}")
                elif ext == ".txt":
                    # Parse plain text
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            text = f.read()
                        documents.append(Document(page_content=text, metadata={"source": str(file_path)}))
                    except Exception as e:
                        print(f"Error reading text file {file_path}: {e}")
    return documents

def create_medical_knowledge_base(embedder):
    documents = load_medical_documents()
    if not documents:
        print("No documents found for knowledge base. Please add files to the data folders.")
        return None
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)
    if not chunks:
        print("No text chunks could be created from the documents. Please check your files.")
        return None
    vectorstore = FAISS.from_documents(chunks, embedder)
    return vectorstore 