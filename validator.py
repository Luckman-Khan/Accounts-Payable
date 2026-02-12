import sqlite3
from pydantic import BaseModel
from thefuzz import process  # pip install thefuzz

# --- 1. CONNECT TO DB ---
def get_db_connection():
    conn = sqlite3.connect('ap_database.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- 2. DEFINE THE RESULT ---
class ValidationResult(BaseModel):
    is_valid: bool
    errors: list[str] = []
    status: str

# --- 3. HELPER: FUZZY VENDOR MATCH ---
def find_best_vendor_match(scanned_name, cursor):
    # Get all valid vendor names
    all_vendors = cursor.execute("SELECT name FROM vendors").fetchall()
    vendor_names = [row['name'] for row in all_vendors]
    
    # Find closest match
    if not vendor_names: return None, 0
    
    match, score = process.extractOne(scanned_name, vendor_names)
    return match, score

# --- 4. HELPER: LINE ITEM CHECK ---
def check_line_items(invoice_items, po_description):
    """
    Returns True if at least one word from the PO description 
    appears in the Invoice Items.
    """
    if not invoice_items: return False
    
    # Simple Keyword Matching
    po_keywords = set(po_description.lower().split())
    
    matches = 0
    for item in invoice_items:
        item_keywords = set(item.lower().split())
        # Check for overlap (e.g. PO="MacBook" matches Item="Apple MacBook Pro")
        if not po_keywords.isdisjoint(item_keywords):
            matches += 1
            
    return matches > 0

# --- 5. MAIN VALIDATION FUNCTION ---
def validate_invoice(invoice_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    errors = []
    
    print(f"🔍 Validating Invoice for PO: {invoice_data.po_number}...")

    # RULE 1: Check Vendor (Fuzzy Match)
    match_name, score = find_best_vendor_match(invoice_data.vendor_name, cursor)
    
    if score < 85: # If confidence is low
        errors.append(f"❌ Vendor '{invoice_data.vendor_name}' not found. (Best match: {match_name} @ {score}%)")
    else:
        print(f"✅ Vendor Verified: {match_name} (Score: {score}%)")

    # RULE 2: Check PO Existence & Line Items
    if invoice_data.po_number:
        po = cursor.execute("SELECT * FROM purchase_orders WHERE po_number = ?", (invoice_data.po_number,)).fetchone()
        
        if not po:
            errors.append(f"❌ PO Number '{invoice_data.po_number}' does not exist.")
        else:
            # RULE 3: Price Check
            if abs(invoice_data.total_amount - po['total_amount']) > 1.0: 
                errors.append(f"⚠️ Price Mismatch: Invoice ${invoice_data.total_amount} vs PO ${po['total_amount']}")
            
            # RULE 4: Line Item Check (New!)
            if not check_line_items(invoice_data.items, po['item_description']):
                 errors.append(f"⚠️ Item Mismatch: Invoice items {invoice_data.items} do not match PO description '{po['item_description']}'")

    else:
        errors.append("⚠️ Missing PO Number on invoice.")

    conn.close()

    # --- DECISION LOGIC ---
    if not errors:
        return ValidationResult(is_valid=True, status="APPROVED", errors=[])
    else:
        return ValidationResult(is_valid=False, status="FLAGGED", errors=errors)