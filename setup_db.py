import sqlite3

def create_database():
    # Connect to (or create) the database file
    conn = sqlite3.connect("ap_database.db")
    cursor = conn.cursor()

    # --- 1. VENDORS TABLE (Updated with typical_price) ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendors (
        vendor_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        contact_email TEXT,
        trust_score INTEGER DEFAULT 50,
        typical_price REAL DEFAULT 0.0  -- Added for Anomaly Detection
    )
    """)

    # --- 2. PURCHASE ORDERS (The "Source of Truth") ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS purchase_orders (
        po_number TEXT PRIMARY KEY,
        vendor_id INTEGER,
        item_description TEXT,
        quantity INTEGER,
        agreed_price_per_unit REAL,
        total_amount REAL,
        status TEXT DEFAULT 'OPEN',
        FOREIGN KEY(vendor_id) REFERENCES vendors(vendor_id)
    )
    """)

    # --- 3. INVOICES ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        invoice_id TEXT PRIMARY KEY,
        po_number TEXT,
        vendor_name_extracted TEXT,
        total_amount_extracted REAL,
        status TEXT DEFAULT 'PROCESSING',
        risk_flag TEXT,
        FOREIGN KEY(po_number) REFERENCES purchase_orders(po_number)
    )
    """)

    # --- 4. AUDIT LOG ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id TEXT,
        action TEXT,
        reason TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # --- DATA SEEDING (Updated with typical_price values) ---
    print("Seeding dummy data with anomaly baselines...")

    # Scenario A: The Good Vendor (Typical price is $5000)
    cursor.execute("""
    INSERT OR IGNORE INTO vendors (vendor_id, name, trust_score, typical_price) 
    VALUES (101, 'TechSupplies Ltd', 95, 5000.0)
    """)
    
    # Scenario B: The Coffee Vendor (Typical price is $1000)
    cursor.execute("""
    INSERT OR IGNORE INTO vendors (vendor_id, name, trust_score, typical_price) 
    VALUES (102, 'Office Coffee Co', 80, 1000.0)
    """)

    # Create POs
    cursor.execute("""
    INSERT OR IGNORE INTO purchase_orders (po_number, vendor_id, item_description, quantity, agreed_price_per_unit, total_amount) 
    VALUES ('PO-001', 101, 'MacBook Pro M3', 5, 1000.0, 5000.0)
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO purchase_orders (po_number, vendor_id, item_description, quantity, agreed_price_per_unit, total_amount) 
    VALUES ('PO-002', 102, 'Premium Coffee Beans', 100, 10.0, 1000.0)
    """)

    conn.commit()
    conn.close()
    print("Database 'ap_database.db' created successfully with Anomaly Detection baselines.")

if __name__ == "__main__":
    create_database()