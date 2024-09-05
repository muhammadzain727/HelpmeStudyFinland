from openai import OpenAI
import os
import base64
from dotenv import load_dotenv
load_dotenv()
MODEL=os.environ.get("MODEL_NAME")
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
client = OpenAI()
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def extract_text_from_image(base64_image):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a transcript analyzer analyzer every subject grades or marks orpoints"},
            {"role": "user", "content": [
                {"type": "text", "text": "What are the name of subjects in Transcripts and thier grades ?"},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"}
                }
            ]}
        ],
        temperature=0.0,
    )

    response_text=response.choices[0].message.content
    return response_text