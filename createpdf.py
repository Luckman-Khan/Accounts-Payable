from fpdf import FPDF
import os

def create_invoice(filename, vendor, date, po_number, items, total, notes=""):
    pdf = FPDF()
    pdf.add_page()
    
    # --- HEADER ---
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"INVOICE from {vendor}", ln=True, align="C")
    pdf.ln(10)
    
    # --- DETAILS ---
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Date: {date}", ln=True)
    pdf.cell(0, 10, f"PO Reference: {po_number}", ln=True)
    pdf.ln(10)
    
    # --- TABLE HEADER ---
    pdf.set_font("Arial", "B", 12)
    pdf.cell(100, 10, "Description", border=1)
    pdf.cell(40, 10, "Amount", border=1, ln=True)
    
    # --- ITEMS ---
    pdf.set_font("Arial", "", 12)
    for item, price in items:
        pdf.cell(100, 10, item, border=1)
        pdf.cell(40, 10, f"${price:,.2f}", border=1, ln=True)
        
    # --- TOTAL ---
    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(100, 10, "TOTAL DUE:", align="R")
    pdf.cell(40, 10, f"${total:,.2f}", border=1, ln=True)
    
    # --- FOOTER ---
    pdf.ln(20)
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(0, 10, f"Notes: {notes}\nThank you for your business.")
    
    pdf.output(filename)
    print(f"✅ Created: {filename}")

# --- GENERATE THE 3 SCENARIOS ---
if __name__ == "__main__":
    
    # 1. THE HAPPY PATH (Matches DB exactly)
    create_invoice(
        filename="invoice_good.pdf",
        vendor="TechSupplies Ltd",
        date="2024-02-12",
        po_number="PO-001",
        items=[("5x MacBook Pro M3", 5000.00)],
        total=5000.00,
        notes="Payment due in 30 days."
    )

    # 2. THE PRICE MISMATCH (Matches PO, but price is wrong)
    create_invoice(
        filename="invoice_bad_price.pdf",
        vendor="TechSupplies Ltd",
        date="2024-02-12",
        po_number="PO-001",
        items=[("5x MacBook Pro M3 (Rush Delivery)", 6500.00)],
        total=6500.00,  # <--- This will trigger the "Price Mismatch" flag
        notes="Includes rush delivery fee."
    )

    # 3. THE FRAUD ATTEMPT (Vendor not in DB)
    create_invoice(
        filename="invoice_fraud.pdf",
        vendor="Evil Corp LLC",  # <--- This will trigger "Unknown Vendor" rejection
        date="2024-02-12",
        po_number="PO-001",
        items=[("Consulting Services", 5000.00)],
        total=5000.00,
        notes="Please pay immediately to Bitcoin wallet..."
    )

    # 4. THE ANOMALY (Correct Vendor/PO, but suspicious price spike)
    create_invoice(
        filename="invoice_anomaly.pdf",
        vendor="TechSupplies Ltd",
        date="2024-02-12",
        po_number="PO-001",
        items=[("5x MacBook Pro M3 (Luxury Gold Edition)", 9000.00)],
        total=9000.00,  # <--- Over 1.5x the $5000 baseline!
        notes="Premium gold-plated finish upgrade."
    )