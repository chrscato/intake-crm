import openai, json, base64
from app.settings import settings
openai.api_key = settings.OPENAI_API_KEY

PROMPT = '''
You are an intake agent for a Workers' Compensation TPA.
Extract claimant_name, claimant_dob, employer_name, injury_date, body_part, referring_provider, service_requested.
Return JSON only.
'''

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
