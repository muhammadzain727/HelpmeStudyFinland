from fastapi import FastAPI, File, UploadFile, Form
from typing import List
import shutil
import os
from fastapi.responses import JSONResponse
from RAG import qa_ret
import uvicorn
from logs import logger
import psycopg2
from analyze_image import *
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
conn = psycopg2.connect(
    dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
)
cursor = conn.cursor()


@app.on_event("startup")
def startup_event():
    try:

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Chatbot (
            id SERIAL PRIMARY KEY,
        );
        
        CREATE TABLE IF NOT EXISTS ChatHistory (
            id SERIAL PRIMARY KEY,
            chat_id INTEGER NOT NULL,
            human_message TEXT NOT NULL,
            ai_message TEXT NOT NULL,
            FOREIGN KEY (chat_id) REFERENCES Chatbot(id)
        );
        """)
        conn.commit()
    except Exception as e:
        logger.error(f"An error occurred {e}")
        return JSONResponse({"error":str(e)})


@app.on_event("shutdown")
def shutdown_event():
    cursor.close()
    conn.close()
    

@app.post("/chat/")
async def chat(chat_id: int = Form(...),query: str = Form(...)):
    try:
        cursor.execute("""
        SELECT human_message, ai_message FROM ChatHistory WHERE chat_id = %s;
        """, (chat_id,))
        chat_history = cursor.fetchall()
        history=[]
        human_messages = [item[0] for item in chat_history]
        ai_messages = [item[1] for item in chat_history]
        for human_message, ai_message in zip(human_messages, ai_messages):
            # history.append(HumanMessage(content=human_message))
            # history.append(AIMessage(content=ai_message))
            history.append(f"question:{human_message}    AImessage:{ai_message}")
        history=" ".join(history)
        response=qa_ret(history,query)
        cursor.execute("SELECT id FROM Chatbot WHERE id = %s", (chat_id,))
        user = cursor.fetchone()
        if user:
            logger.info("User authenticated successfully")
        else:
            cursor.execute("INSERT INTO Chatbot (id) VALUES (%s,%s)", (chat_id))
            conn.commit()
        cursor.execute("""
        INSERT INTO ChatHistory (chat_id, human_message, ai_message)
        VALUES (%s, %s, %s) RETURNING id;
        """, (chat_id, query, response))
        chat_id = cursor.fetchone()[0]
        conn.commit()
        return {
            "user_qeury":query,
            "tittle":tittle,
            "response":response
        }
    except Exception as e:
        logger.error(f"An error occurred {e}")
        return JSONResponse({"error":str(e)})
    


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

if __name__ == "__main__":
    
    uvicorn.run(app, host="127.0.0.1", port=4400)
