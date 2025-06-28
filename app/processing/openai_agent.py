import json
import base64
from pathlib import Path
import openai
import fitz  # PyMuPDF

from app.settings import settings

openai.api_key = settings.OPENAI_API_KEY

# Load the GPT-4o prompt from the adjacent JSON file
PROMPT_PATH = Path(__file__).with_name("gpt4o_prompt.json")
with open(PROMPT_PATH, "r", encoding="utf-8") as f:
    PROMPT = json.load(f)["prompt"]


def parse_json_from_response(text: str) -> dict:
    """Parse a JSON string that may be wrapped in triple backtick fences."""
    cleaned = text.strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
        cleaned = cleaned[3:-3].strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].lstrip()
    return json.loads(cleaned)

def pdf_to_b64_images(pdf_bytes: bytes, max_dim_px: int = 2200, jpeg_q: int = 80) -> list[str]:
    """Render each PDF page to base64-encoded JPEG."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    for pg in doc:
        pix = pg.get_pixmap(dpi=200)
        if pix.width > max_dim_px:  # downscale huge scans
            scale = max_dim_px / pix.width
            pix = pg.get_pixmap(matrix=fitz.Matrix(scale, scale))
        pages.append(base64.b64encode(
            pix.tobytes("jpg", jpg_quality=jpeg_q)).decode())
    doc.close()
    return pages

def extract(file_bytes: bytes, email_body: str, file_extension: str = ".pdf"):
    """Extract structured data from file attachments using OpenAI GPT-4o-mini.
    
    Args:
        file_bytes: Raw bytes of the file
        email_body: Text content of the email
        file_extension: File extension to determine content type
    """
    print(f"🔧 DEBUG: Starting extraction for {file_extension} file")
    print(f"🔧 DEBUG: File size: {len(file_bytes)} bytes")
    print(f"🔧 DEBUG: Email body length: {len(email_body)} characters")
    print(f"🔧 DEBUG: OpenAI API Key set: {'✅' if settings.OPENAI_API_KEY else '❌'}")
    
    if file_extension.lower() == '.pdf':
        print(f"🔧 DEBUG: Processing PDF file")
        # Convert PDF to image(s) using PyMuPDF
        try:
            print(f"🔧 DEBUG: Converting PDF to images...")
            # Get all pages as base64 images
            page_images = pdf_to_b64_images(file_bytes)
            print(f"🔧 DEBUG: PDF converted to {len(page_images)} page(s)")
            
            # For now, just process the first page
            # You could extend this to process multiple pages if needed
            base64_data = page_images[0]
            print(f"🔧 DEBUG: Using first page, base64 length: {len(base64_data)}")
            
        except Exception as e:
            print(f"🔧 DEBUG: PDF conversion failed: {e}")
            raise ValueError(f"Failed to convert PDF to image: {e}")
            
    elif file_extension.lower() in ['.png', '.jpg', '.jpeg']:
        print(f"🔧 DEBUG: Processing image file directly")
        # Images can be processed directly
        base64_data = base64.b64encode(file_bytes).decode()
        print(f"🔧 DEBUG: Image base64 length: {len(base64_data)}")
    else:
        print(f"🔧 DEBUG: Unsupported file type: {file_extension}")
        raise ValueError(f"Unsupported file type: {file_extension}")
    
    # Use the vision API for all file types (now all are images)
    print(f"🔧 DEBUG: Preparing OpenAI API call...")
    print(f"🔧 DEBUG: Using model: gpt-4o-mini")
    print(f"🔧 DEBUG: Max tokens: 1024")
    print(f"🔧 DEBUG: Email body preview: {email_body[:100]}...")
    
    try:
        print(f"🔧 DEBUG: Making OpenAI API call...")
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1024,
            messages=[
                { "role": "system", "content": PROMPT },
                { "role": "user",
                  "content": [
                     { "type": "text", "text": email_body[:4000]},
                     { "type": "image_url", 
                       "image_url": {
                           "url": f"data:image/jpeg;base64,{base64_data}"
                       }
                     }
                  ]}
            ]
        )
        
        print(f"🔧 DEBUG: OpenAI API call completed")
        print(f"🔧 DEBUG: Response object type: {type(response)}")
        print(f"🔧 DEBUG: Number of choices: {len(response.choices)}")
        
        if response.choices:
            content = response.choices[0].message.content
            print(f"🔧 DEBUG: Response content length: {len(content) if content else 0}")
            print(f"🔧 DEBUG: Response content preview: {content[:200] if content else 'EMPTY'}...")
            
            # Check if response is empty
            if not content:
                print(f"🔧 DEBUG: ERROR - OpenAI returned empty response")
                raise ValueError("OpenAI returned empty response")
                
            print(f"🔧 DEBUG: Attempting to parse JSON...")
            parsed_data = parse_json_from_response(content)
            print(f"🔧 DEBUG: JSON parsing successful")
            print(f"🔧 DEBUG: Parsed data keys: {list(parsed_data.keys()) if isinstance(parsed_data, dict) else 'Not a dict'}")
            return parsed_data
        else:
            print(f"🔧 DEBUG: ERROR - No choices in response")
            raise ValueError("No choices in OpenAI response")
            
    except json.JSONDecodeError as e:
        print(f"🔧 DEBUG: JSON Decode Error: {e}")
        print(f"🔧 DEBUG: Raw response content: {response.choices[0].message.content if response.choices and response.choices[0].message.content else 'EMPTY'}")
        raise ValueError(f"Failed to parse JSON response: {e}")
    except Exception as e:
        print(f"🔧 DEBUG: OpenAI API Error: {e}")
        print(f"🔧 DEBUG: Error type: {type(e)}")
        raise ValueError(f"OpenAI API error: {e}")
