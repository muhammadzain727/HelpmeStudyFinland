from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from openai import OpenAI
from dotenv import load_dotenv
from io import BytesIO
import base64
import os
import fitz  # PyMuPDF for PDF text extraction
import uvicorn
from docx import Document  # For DOCX file handling

# Load environment variables from .env file
load_dotenv()

# Set up OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)
MODEL = "gpt-4o"

app = FastAPI()

def encode_image(image_bytes):
    """Encode an image file in base64 format."""
    return base64.b64encode(image_bytes).decode("utf-8")

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

@app.post("/analyze-lor/")
async def analyze_lor(file: UploadFile = File(...)):
    try:
        # Read the uploaded file
        file_content = await file.read()

        if file.content_type == "application/pdf":
            # Extract text from PDF
            extracted_text = extract_text_from_pdf(file_content)
            prompt_content = (
                f"Analyze the following Letter of Recommendation (LoR) or letter of motivation. "
                f"Provide two sections in your response: \n\n"
                f"**Rating**: Provide a rating out of 10 based on the quality of the letter.\n"
                f"**Suggestions**: Suggest 3 to 5 specific improvements to enhance the letter's effectiveness. Each suggestion should be short, specific, and in point format.\n\n"
                f"Text to analyze:\n{extracted_text}"
            )
        elif file.content_type in ["image/jpeg", "image/png"]:
            # Encode the image to base64
            base64_image = encode_image(file_content)
            prompt_content = (
                "Analyze the text in this image of a Letter of Recommendation (LoR) or letter of motivation. "
                "Provide two sections in your response: \n\n"
                "**Rating**: Provide a rating out of 10 based on the quality of the letter.\n"
                "**Suggestions**: Suggest 3 to 5 specific improvements to enhance the letter's effectiveness. "
                "Each suggestion should be short, specific, and in point format."
            )
            image_data = f"data:image/png;base64,{base64_image}" if file.content_type == "image/png" else f"data:image/jpeg;base64,{base64_image}"
        elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            # Extract text from DOCX
            extracted_text = extract_text_from_docx(file_content)
            prompt_content = (
                f"Analyze the following Letter of Recommendation (LoR) or letter of motivation. "
                f"Provide two sections in your response: \n\n"
                f"**Rating**: Provide a rating out of 10 based on the quality of the letter.\n"
                f"**Suggestions**: Suggest 3 to 5 specific improvements to enhance the letter's effectiveness. Each suggestion should be short, specific, and in point format.\n\n"
                f"Text to analyze:\n{extracted_text}"
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a PDF, DOCX, JPG, or PNG file.")

        # Prepare the OpenAI API request
        messages = [{"role": "system", "content": "You are an expert in document analysis, tasked with analyzing Letters of Recommendation and letters of motivation. Provide a rating and suggestions for improvement."}]
        if file.content_type in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            messages.append({"role": "user", "content": prompt_content})
        else:
            messages.append({
                "role": "user", 
                "content": [
                    {"type": "text", "text": prompt_content},
                    {"type": "image_url", "image_url": {"url": image_data}}
                ]
            })

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.0,
        )

        # Extract and return the response from OpenAI
        result = response.choices[0].message.content
        return JSONResponse(content={"analysis": result})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# To run the app use: uvicorn app:app --reload
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9292)
