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

if __name__ == "__main__":
    
    # 1. THE AUTO-PAY (Matches PO-002, Under $1k limit)
    # Result: ✅ APPROVED & PAID INSTANTLY
    create_invoice(
        filename="invoice_autopay.pdf",
        vendor="Office Coffee Co",
        date="2024-02-12",
        po_number="PO-002",
        items=[("100kg Premium Coffee Beans", 500.00)],
        total=500.00,
        notes="Recurring monthly order."
    )

    # 2. THE HIGH VALUE (Matches PO-001, but > $1k limit)
    # Result: ⚖️ FLAGGED (Needs Manager Approval)
    create_invoice(
        filename="invoice_high_value.pdf",
        vendor="TechSupplies Ltd",
        date="2024-02-12",
        po_number="PO-001",
        items=[("5x MacBook Pro M3", 5000.00)],
        total=5000.00,
        notes="Equipment for Engineering Team."
    )

    # 3. THE PRICE SPIKE (Matches PO-001, but price is way off)
    # Result: 🚨 REJECTED (Price Anomaly > 1.5x baseline)
    create_invoice(
        filename="invoice_anomaly.pdf",
        vendor="TechSupplies Ltd",
        date="2024-02-12",
        po_number="PO-001",
        items=[("5x MacBook Pro M3 (Gold Plated)", 9000.00)],
        total=9000.00,
        notes="Special request upgrade."
    )

    # 4. THE FRAUD (Vendor not in DB)
    # Result: 🚫 REJECTED (Unknown Vendor)
    create_invoice(
        filename="invoice_fraud.pdf",
        vendor="Evil Corp LLC",
        date="2024-02-12",
        po_number="PO-001",
        items=[("Consulting Services", 1000.00)],
        total=1000.00,
        notes="Wire transfer immediately."
    )

    # 5. THE PO MISMATCH (Vendor OK, Price OK, but PO is wrong)
    # Result: ⚠️ FLAGGED/REJECTED (PO Not Found)
    create_invoice(
        filename="invoice_bad_po.pdf",
        vendor="Office Coffee Co",
        date="2024-02-12",
        po_number="PO-999", # <--- Does not exist
        items=[("Coffee Beans", 1000.00)],
        total=1000.00,
        notes="Urgent order."
    )