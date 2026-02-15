import csv
import os
from datetime import datetime

LEDGER_FILE = "company_general_ledger.csv"

def log_to_ledger(vendor_name, amount, currency, invoice_ref, transfer_id):
    """
    Appends a new transaction row to the General Ledger.
    """
    # Define GL Codes based on Vendor (Simplified AI Categorization)
    gl_mapping = {
        "TechSupplies Ltd": "6001 - Hardware/IT Expense",
        "Office Coffee Co": "6105 - Office Supplies",
        "Evil Corp LLC": "9999 - SUSPICIOUS/UNMAPPED"
    }
    
    gl_code = gl_mapping.get(vendor_name, "6000 - General Expense")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    file_exists = os.path.isfile(LEDGER_FILE)

    print(f"📒 Syncing to Ledger: {invoice_ref}...")

    with open(LEDGER_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        
        if not file_exists:
            writer.writerow(["Timestamp", "Vendor", "Amount", "Currency", "GL Code", "PO Reference", "Stripe ID", "Status"])
        
        writer.writerow([
            timestamp, 
            vendor_name, 
            amount, 
            currency.upper(), 
            gl_code, 
            invoice_ref, 
            transfer_id, 
            "POSTED"
        ])

    print(f"✅ Transaction {transfer_id} recorded in General Ledger.")