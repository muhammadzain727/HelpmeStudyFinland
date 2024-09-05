from fastapi import FastAPI, File, UploadFile, Form
from typing import List
from fastapi.responses import JSONResponse
import uvicorn
from logs import logger
from manage_database_operations import *
from RAG import *
from document_loaders import *
from image_to_text import *
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()


@app.post("/api/helpmestudyfinland/AIconsultant")
async def chat(chat_id:int,query: str):
    try:
        # Fetch chat history

        history=fetch_chat_history(chat_id)
        summerize_history=history_summerizer(history)
        response = ai_consultant(summerize_history, query)
        insert_chat_history(chat_id,query,response)

        return {
            "user_query": query,
            "response": response,
        }
    except Exception as e:
        logger.error(f"An error occurred {e}")
        return JSONResponse({"error": str(e)}, status_code=500)
    

@app.post("/api/helpmestudyfinland/LetterOfMotivationEvaluator")
async def analyze_lor(name_of_program:str,program_description:str,file: UploadFile = File(...)):
    try:
        # Ensure the file type is either PDF or DOCX
        if file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            raise JSONResponse(status_code=400, detail="Unsupported file type. Please upload a PDF or DOCX file.")

        # Read the uploaded file
        file_content = await file.read()

        if file.content_type == "application/pdf":
            # Extract text from PDF
            extracted_text = extract_text_from_pdf(file_content)
        elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            # Extract text from DOCX
            extracted_text = extract_text_from_docx(file_content)


        # Extract and return the response from OpenAI
        result = analyze_letter_of_motivation(name_of_program,program_description,extracted_text)
        return JSONResponse(content={"analysis": result})

    except Exception as e:
        return JSONResponse(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/api/helpmestudyfinland/AcademicRecordEvaluator")
async def analyze_lor(name_of_program: str, program_description: str, file: UploadFile = File(...)):
    try:
        # Ensure the file type is either PNG or JPG
        if file.content_type not in ["image/png", "image/jpeg"]:
            raise JSONResponse(status_code=400, detail="Unsupported file type. Please upload a PNG or JPG file.")
        # Read the uploaded file
        # file_content = await file.read()
        image_file=file.filename
        base64_image=encode_image(image_file)
        image_text=extract_text_from_image(base64_image)

        # Extract and return the response from OpenAI
        result = transcript_evaluation(name_of_program, program_description, image_text)
        return JSONResponse(content={"analysis": result})

    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"An error occurred: {str(e)}"}) 

    
@app.post("/api/helpmestudyfinland/ResumeEvaluator")
async def analyze_lor(name_of_program:str,program_description:str,file: UploadFile = File(...)):
    try:
        # Ensure the file type is either PDF or DOCX
        if file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            raise JSONResponse(status_code=400, detail="Unsupported file type. Please upload a PDF or DOCX file.")

        # Read the uploaded file
        file_content = await file.read()

        if file.content_type == "application/pdf":
            # Extract text from PDF
            extracted_text = extract_text_from_pdf(file_content)
        elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            # Extract text from DOCX
            extracted_text = extract_text_from_docx(file_content)


        # Extract and return the response from OpenAI
        result = resume_evaluation(name_of_program,program_description,extracted_text)
        return JSONResponse(content={"analysis": result})

    except Exception as e:
        return JSONResponse(status_code=500, detail=f"An error occurred: {str(e)}")
    
@app.delete("/api/helpmestudyfinland/DeleteChat")
async def analyze_lor(chat_id:int):
    try:
        chat_deleted=delete_chat_history(chat_id)
        return JSONResponse(content={"message": chat_deleted})
    except Exception as e:
        return JSONResponse(status_code=500, detail=f"An error occurred: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9393)