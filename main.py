from fastapi import FastAPI, File, UploadFile, Form
from typing import List
import shutil
import os
from fastapi.responses import JSONResponse
from RAG import qa_ret
import uvicorn
from logs import logger
import psycopg2
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
            tittle VARCHAR(200) NOT NULL
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
async def chat(user_id: int = Form(...),username: str = Form(...),query: str = Form(...)):
    """
    Handles incoming chat queries, processes them using a question answering system,
    and returns the response.

    Args:
        query (str): The user query string to process.

    Returns:
        dict: A dictionary containing the response to the query.
            Example:
            {
                "response": "The answer to the user's query."
            }

        If an error occurs during processing, returns:
            {
                "error": "Error details."
            }
    """
    try:
        cursor.execute("""
        SELECT human_message, ai_message FROM ChatHistory WHERE user_id = %s;
        """, (user_id,))
        chat_history = cursor.fetchall()
        history=[]
        human_messages = [item[0] for item in chat_history]
        ai_messages = [item[1] for item in chat_history]
        for human_message, ai_message in zip(human_messages, ai_messages):
            # history.append(HumanMessage(content=human_message))
            # history.append(AIMessage(content=ai_message))
            history.append(f"question:{human_message}    AImessage:{ai_message}")
        history=" ".join(history)
        response=qa_ret(history,index_name,query)
        cursor.execute("SELECT id FROM Chatbot WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if user:
            logger.info("User authenticated successfully")
        else:
            cursor.execute("INSERT INTO Chatbot (id,tittle) VALUES (%s,%s)", (user_id,username))
            conn.commit()
        cursor.execute("""
        INSERT INTO ChatHistory (chat_id, human_message, ai_message)
        VALUES (%s, %s, %s) RETURNING id;
        """, (user_id, query, response))
        chat_id = cursor.fetchone()[0]
        conn.commit()
        return {
            "user_qeury":query,
            "response":response
        }
    except Exception as e:
        logger.error(f"An error occurred {e}")
        return JSONResponse({"error":str(e)})

if __name__ == "__main__":
    
    uvicorn.run(app, host="127.0.0.1", port=4400)
