import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()
# Set up database connection using environment variables


def fetch_chat_history(chat_id):
    conn = psycopg2.connect(
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    host=os.environ.get("DB_HOST"),
    port=os.environ.get("DB_PORT")
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT human_message, ai_message FROM ChatHistory 
            WHERE chat_id = %s
            ORDER BY id DESC
            LIMIT 5;
            """, (chat_id,))
            chat_history = cursor.fetchall()

            history = []
            for human_message, ai_message in chat_history:
                history.append(f"question:{human_message}    AImessage:{ai_message}")
            history = " ".join(history)

            return history

    except Exception as e:
        raise e


def insert_chat_history(chat_id, query, response):
    conn = psycopg2.connect(
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    host=os.environ.get("DB_HOST"),
    port=os.environ.get("DB_PORT")
    )
    try:
        with conn.cursor() as cursor:
            # Check if the chat_id exists in the Chatbot table
            cursor.execute("SELECT id FROM Chatbot WHERE id = %s", (chat_id,))
            chats = cursor.fetchone()

            if not chats:
                # Insert a new entry into the Chatbot table if it doesn't exist
                cursor.execute("INSERT INTO Chatbot (id) VALUES (%s)", (chat_id,))
                conn.commit()

            # Insert the new chat entry into the ChatHistory table
            cursor.execute("""
            INSERT INTO ChatHistory (chat_id, human_message, ai_message)
            VALUES (%s, %s, %s) RETURNING id;
            """, (chat_id, query, response))
            conn.commit()

            # Fetch and print the inserted record ID (optional)
            inserted_id = cursor.fetchone()[0]
            print(f"Inserted chat history with ID: {inserted_id}")

    except Exception as e:
        print(e)


def delete_chat_history(chat_id):
    conn = psycopg2.connect(
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    host=os.environ.get("DB_HOST"),
    port=os.environ.get("DB_PORT")
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
            DELETE FROM chathistory 
            WHERE chat_id = %s;
            """, (chat_id,))
            conn.commit()
            return "Chat History Deleted Successfully"
    except Exception as e:
        raise e