from io import BytesIO
import fitz  # PyMuPDF for PDF text extraction
from docx import Document # For DOCX file handling
from langchain_community.document_loaders import PyMuPDFLoader
def extract_text_from_pdf(pdf_bytes):
    """Extract text from a PDF file."""
    text = ""
    pdf_stream = BytesIO(pdf_bytes)
    pdf_document = fitz.open(stream=pdf_stream, filetype="pdf")
    for page in pdf_document:
        text += page.get_text()
    pdf_document.close()
    return text

def extract_text_from_docx(docx_bytes):
    """Extract text from a DOCX file."""
    text = ""
    doc_stream = BytesIO(docx_bytes)
    document = Document(doc_stream)
    for para in document.paragraphs:
        text += para.text + "\n"
    return text