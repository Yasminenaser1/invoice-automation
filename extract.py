import json
import sys
import time
from pathlib import Path
from google import genai
from google.genai import types, errors
from dotenv import load_dotenv

load_dotenv()
client = genai.Client()  # reads GEMINI_API_KEY from .env
MODEL = "gemini-3.8-flash"

# File extension -> the label Gemini needs to understand the file
MIME_TYPES = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}

PROMPT = """You are reading an invoice. Extract these fields and return JSON only:
{
  "vendor_name": string,
  "invoice_number": string,
  "invoice_date": "YYYY-MM-DD",
  "customer_name": string,
  "line_items": [{"description": string, "quantity": number, "unit_price": number, "amount": number}],
  "subtotal": number,
  "tax": number,
  "total": number
}
If a field is not on the invoice, use null."""

def call_with_retry(fn, max_attempts=5):
    """Run fn(). If the server is busy, wait longer each time and try again."""
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except errors.ServerError as e:
            if attempt == max_attempts:
                raise
            wait = 2 ** attempt  # 2, 4, 8, 16 seconds
            print(f"Server busy ({e.code}). Attempt {attempt} failed, retrying in {wait}s...")
            time.sleep(wait)

def extract_invoice(file_path):
    suffix = Path(file_path).suffix.lower()
    if suffix not in MIME_TYPES:
        raise ValueError(f"Unsupported file type: {suffix} (supported: {', '.join(MIME_TYPES)})")

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    def request():
        return client.models.generate_content(
            model=MODEL,
            contents=[
                types.Part.from_bytes(data=file_bytes, mime_type=MIME_TYPES[suffix]),
                PROMPT,
            ],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )

    response = call_with_retry(request)
    return json.loads(response.text)

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "invoices/INV-1001.pdf"
    data = extract_invoice(path)
    print(json.dumps(data, indent=2))
