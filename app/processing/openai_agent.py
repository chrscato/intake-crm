import json
import base64
from pathlib import Path
import openai

from app.settings import settings

openai.api_key = settings.OPENAI_API_KEY

# Load the GPT-4o prompt from the adjacent JSON file
PROMPT_PATH = Path(__file__).with_name("gpt4o_prompt.json")
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    PROMPT = json.load(f)["prompt"]

def extract(pdf_bytes: bytes, email_body: str):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1024,
        messages=[
            { "role": "system", "content": PROMPT },
            { "role": "user",
              "content": [
                 { "type": "text", "text": email_body[:4000]},
                 { "type": "image", "data": base64.b64encode(pdf_bytes).decode(),
                   "mime_type": "application/pdf" }
              ]}
        ]
    )
    return json.loads(response.choices[0].message.content)
