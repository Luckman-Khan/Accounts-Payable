import os
import json
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import Optional, List

# --- 1. DEFINE THE OUTPUT FORMAT (The Contract) ---
class InvoiceData(BaseModel):
    vendor_name: str = Field(description="Name of the vendor")
    invoice_date: str = Field(description="Date in YYYY-MM-DD format")
    total_amount: float = Field(description="Total amount due")
    currency: str = Field(description="Currency code (USD, GBP)", default="USD")
    po_number: Optional[str] = Field(description="PO Number if found", default=None)
    items: List[str] = Field(description="List of line items", default_factory=list)

# --- 2. THE EXTRACTION FUNCTION ---
def extract_invoice_from_text(invoice_text: str, api_key: str = None):
    # Auto-load API key if not passed
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("⚠️ No API Key. Using Mock Data.")
        return InvoiceData(vendor_name="Mock Vendor", invoice_date="2024-01-01", total_amount=100.0, items=[])

    # Configure Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash',
        generation_config={"response_mime_type": "application/json"}
    )

    # --- THE FIX: STRICTER PROMPT ---
    prompt = f"""
    You are a data extraction API. Extract the following fields from the invoice text below.
    Return ONLY a JSON object. Do not invent new keys. Use EXACTLY these keys:
    
    {{
        "vendor_name": "string",
        "invoice_date": "YYYY-MM-DD",
        "total_amount": float,
        "currency": "string",
        "po_number": "string (or null)",
        "items": ["string", "string"]
    }}

    INVOICE TEXT:
    {invoice_text}
    """

    try:
        response = model.generate_content(prompt)
        data = json.loads(response.text)
        
        # Ensure 'items' is always a list (AI sometimes makes it a string)
        if "items" in data and isinstance(data["items"], str):
            data["items"] = [data["items"]]
            
        return InvoiceData(**data)
    except Exception as e:
        print(f"Error extracting data: {e}")
        return None