import json
import fitz
import docx

class Data_Extractor:
    def extract_text(uploaded_file):
        file_type = uploaded_file.type
        name = uploaded_file.name.lower()

        if file_type == "application/pdf" or name.endswith(".pdf"):
            with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
                return "\n".join([page.get_text() for page in doc])
        elif file_type == "text/plain" or name.endswith(".txt"):
            return uploaded_file.read().decode("utf-8")
        elif file_type == "application/json" or name.endswith(".json"):
            data = json.load(uploaded_file)
            return json.dumps(data, indent=2)
        elif name.endswith(".docx"):
            from docx import Document
            doc = Document(uploaded_file)
            return "\n".join([para.text for para in doc.paragraphs])
        return "⚠️ Unsupported file type."

    def preprocess_resume_text(text):
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
        return text
