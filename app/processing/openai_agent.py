import json
import base64
from pathlib import Path
import openai
import fitz  # PyMuPDF

from app.settings import settings

openai.api_key = settings.OPENAI_API_KEY

def generate_dynamic_prompt() -> str:
    """Generate the prompt dynamically from the sample structure."""
    # Load the sample structure
    sample_path = Path(__file__).with_name("sample.json")
    if not sample_path.exists():
        raise FileNotFoundError(f"Sample file not found: {sample_path}")
    
    with open(sample_path, "r", encoding="utf-8") as f:
        sample_data = json.load(f)
    
    # Extract field names from the sample
    field_names = list(sample_data.keys())
    print(f"🔧 DEBUG: Using {len(field_names)} fields from sample: {field_names}")
    
    # Generate the dynamic prompt with consolidation instructions
    base_prompt = """You are an intake agent for a Workers' Compensation TPA. You will be provided with an email and multiple attachments (images/PDFs). 

Your task is to analyze ALL the provided evidence (email text + all attachments) and determine whether this describes a request to refer an injured worker for medical services such as radiology, EMG, EKG, and/or DME.

IMPORTANT: You must consolidate information from ALL sources (email + all attachments) into a single comprehensive record. If information appears in multiple sources, choose the most complete/accurate version. If information conflicts between sources, use your judgment to select the most reliable information.

If it is not a referral request, reply with {"referral": false}. If it is, reply with JSON using the keys below, leaving a value null when unsure. Fields that may contain multiple values should be arrays."""
    
    field_list = "\n".join([f"- {field}" for field in field_names])
    
    full_prompt = f"{base_prompt}\n{field_list}\nReturn only JSON."
    
    return full_prompt

# Generate the prompt dynamically
PROMPT = generate_dynamic_prompt()

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

def extract_consolidated(file_bytes_list: list[bytes], email_body: str, file_extensions: list[str]):
    """Extract structured data from multiple file attachments using OpenAI GPT-4o-mini.
    
    This function processes all attachments together to generate a single consolidated output.
    
    Args:
        file_bytes_list: List of raw bytes for each file
        email_body: Text content of the email
        file_extensions: List of file extensions to determine content types
    """
    print(f"🔧 DEBUG: Starting consolidated extraction for {len(file_bytes_list)} files")
    print(f"🔧 DEBUG: Email body length: {len(email_body)} characters")
    print(f"🔧 DEBUG: OpenAI API Key set: {'✅' if settings.OPENAI_API_KEY else '❌'}")
    
    # Convert all files to base64 images
    base64_images = []
    
    for i, (file_bytes, extension) in enumerate(zip(file_bytes_list, file_extensions)):
        print(f"🔧 DEBUG: Processing file {i+1}/{len(file_bytes_list)}: {extension}")
        
        if extension.lower() == '.pdf':
            print(f"🔧 DEBUG: Converting PDF to images...")
            try:
                # Get all pages as base64 images
                page_images = pdf_to_b64_images(file_bytes)
                print(f"🔧 DEBUG: PDF converted to {len(page_images)} page(s)")
                
                # For now, just use the first page of each PDF
                # You could extend this to process multiple pages if needed
                base64_images.append(page_images[0])
                print(f"🔧 DEBUG: Added PDF page, base64 length: {len(page_images[0])}")
                
            except Exception as e:
                print(f"🔧 DEBUG: PDF conversion failed: {e}")
                raise ValueError(f"Failed to convert PDF to image: {e}")
                
        elif extension.lower() in ['.png', '.jpg', '.jpeg']:
            print(f"🔧 DEBUG: Processing image file directly")
            # Images can be processed directly
            base64_data = base64.b64encode(file_bytes).decode()
            base64_images.append(base64_data)
            print(f"🔧 DEBUG: Image base64 length: {len(base64_data)}")
        else:
            print(f"🔧 DEBUG: Unsupported file type: {extension}")
            raise ValueError(f"Unsupported file type: {extension}")
    
    # Prepare content for OpenAI API call
    content = [
        {"type": "text", "text": email_body[:4000]}
    ]
    
    # Add all images to the content
    for i, base64_data in enumerate(base64_images):
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_data}"
            }
        })
    
    print(f"🔧 DEBUG: Prepared content with {len(content)} items (1 text + {len(base64_images)} images)")
    
    # Use the vision API for all file types (now all are images)
    print(f"🔧 DEBUG: Preparing OpenAI API call...")
    print(f"🔧 DEBUG: Using model: gpt-4o-mini")
    print(f"🔧 DEBUG: Max tokens: 2048")  # Increased for consolidated processing
    
    try:
        print(f"🔧 DEBUG: Making OpenAI API call...")
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=2048,  # Increased for consolidated processing
            messages=[
                { "role": "system", "content": PROMPT },
                { "role": "user", "content": content }
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

def extract(file_bytes: bytes, email_body: str, file_extension: str = ".pdf"):
    """Legacy function for single file extraction - now calls consolidated version."""
    return extract_consolidated([file_bytes], email_body, [file_extension])
