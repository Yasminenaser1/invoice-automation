import json
import time
from google import genai
from google.genai import types, errors

from dotenv import load_dotenv
load_dotenv()
client = genai.Client()  # reads GEMINI_API_KEY automatically
MODEL = "gemini-3.8-flash"

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

def extract_invoice(pdf_path):
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    def request():
        return client.models.generate_content(
            model=MODEL,
            contents=[
                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                PROMPT,
            ],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )

    response = call_with_retry(request)
    return json.loads(response.text)

if __name__ == "__main__":
    data = extract_invoice("invoices/INV-1001.pdf")
    print(json.dumps(data, indent=2))
