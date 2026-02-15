import os
import json
from dotenv import load_dotenv
from typing import Optional
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI 
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

load_dotenv()

class InvoiceData(BaseModel):
    vendor_name: str = Field(description="Name of the vendor")
    po_number: Optional[str] = Field(description="PO Number if found, else null")
    total_amount: float = Field(description="Total amount as a number")
    currency: str = Field(description="Currency code (USD, INR, EUR)")
    date: str = Field(description="Invoice date in YYYY-MM-DD format")
    items: list[str] = Field(description="List of item descriptions")

def extract_invoice_from_text(invoice_text: str) -> InvoiceData:
    """
    Uses LangChain + Gemini to extract structured data from invoice text.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY missing in .env")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=api_key
    )

    parser = JsonOutputParser(pydantic_object=InvoiceData)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert financial data extractor. Extract the following invoice data exactly."),
        ("user", "Invoice Text:\n{invoice_text}\n\n{format_instructions}")
    ])

    chain = prompt | llm | parser

    try:
        result = chain.invoke({
            "invoice_text": invoice_text,
            "format_instructions": parser.get_format_instructions()
        })
        return InvoiceData(**result)
    except Exception as e:
        print(f"❌ Extraction Error: {e}")
        return None