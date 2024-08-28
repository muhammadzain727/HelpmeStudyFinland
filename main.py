from fastapi import FastAPI, File, UploadFile, Form
from typing import List
import shutil
import os
from fastapi.responses import JSONResponse
import uvicorn
from logs import logger
from manage_database_operations import *
from RAG  import *
from letter_of_mot_and_rec import *
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()


@app.post("/chat/")
async def chat(chat_id:int,query: str):
    try:
        # Fetch chat history

        history=fetch_chat_history(chat_id)
        # Process the current query
        response = qa_ret(history, query)

        insert_chat_history(chat_id,query,response)

        return {
            "user_query": query,
            "response": response,
        }
    except Exception as e:
        logger.error(f"An error occurred {e}")
        return JSONResponse({"error": str(e)}, status_code=500)
    
@app.post("/analyze-lor/")
async def analyze_lor(file: UploadFile = File(...)):
    try:
        # Ensure the file type is either PDF or DOCX
        if file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a PDF or DOCX file.")

        # Read the uploaded file
        file_content = await file.read()

        if file.content_type == "application/pdf":
            # Extract text from PDF
            extracted_text = extract_text_from_pdf(file_content)
        elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            # Extract text from DOCX
            extracted_text = extract_text_from_docx(file_content)


        # Extract and return the response from OpenAI
        result = analyze_document(extracted_text)
        return JSONResponse(content={"analysis": result})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9393)
