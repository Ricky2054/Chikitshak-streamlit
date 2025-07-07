from langchain_community.embeddings import OllamaEmbeddings
# For future: from langchain_ollama import OllamaEmbeddings (see deprecation warning)

def get_embedder(model="nomic-embed-text"):
    return OllamaEmbeddings(model=model)

class MultimodalMedicalRAG:
    def __init__(self):
        self.text_embeddings = OllamaEmbeddings(model="nomic-embed-text")
        # self.image_processor = MedicalImageProcessor()  # Placeholder for image processor
    
    def process_medical_document(self, file):
        if hasattr(file, 'type') and file.type == "application/pdf":
            return self.process_pdf(file)
        elif hasattr(file, 'type') and file.type.startswith("image/"):
            return self.process_image(file)
        else:
            return self.process_text(file)
    
    def process_pdf(self, file):
        # TODO: Implement PDF processing
        pass
    def process_image(self, file):
        # TODO: Implement image processing
        pass
    def process_text(self, file):
        # TODO: Implement text processing
        pass 