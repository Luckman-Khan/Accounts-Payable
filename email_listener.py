import imaplib
import email
from email.header import decode_header
import os
import time
import shutil
from dotenv import load_dotenv
from pypdf import PdfReader
from agent import app as agent_app 
import requests
import json
from payment_manager import process_payment
from accounting_sync import log_to_ledger


load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
IMAP_SERVER = "imap.gmail.com"
SLACK_URL = os.getenv("SLACK_WEBHOOK_URL")

# Setup Directories
INPUT_DIR = "./invoices_input"
PAID_DIR = "./processed/paid"
FAILED_PAY_DIR = "./processed/failed_payments"
FLAGGED_DIR = "./processed/flagged"


for folder in [PAID_DIR, FLAGGED_DIR, FAILED_PAY_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)


def send_slack_alert(filename, reason, details):
    """
    Sends a high-priority alert to Slack with specific anomaly details.
    """
    # Use SLACK_WEBHOOK_URL from your .env
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("⚠️ Slack URL missing in .env")
        return

    # Severity icon logic
    icon = "🚨" if reason in ["PRICE_ANOMALY", "REJECTED"] else "⚠️"
    
    payload = {
        "text": f"{icon} *Invoice Action Required*\n"
                f"*File:* `{filename}`\n"
                f"*Status:* `{reason}`\n"
                f"*Details:* {details}"
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            print("🔔 Slack Alert Sent!")
        else:
            print(f"⚠️ Slack returned error: {response.status_code}")
    except Exception as e:
        print(f"Error sending Slack alert: {e}")


def get_pdf_text(filepath):
    try:
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        print(f"❌ Corrupt PDF: {e}")
        return None

def move_file(filepath, dest_folder):
    """Moves file to destination, adding timestamp if file already exists"""
    filename = os.path.basename(filepath)
    dest_path = os.path.join(dest_folder, filename)
    
    # If file exists, rename it (invoice.pdf -> invoice_1.pdf)
    if os.path.exists(dest_path):
        base, ext = os.path.splitext(filename)
        timestamp = int(time.time())
        dest_path = os.path.join(dest_folder, f"{base}_{timestamp}{ext}")
        
    shutil.move(filepath, dest_path)

def process_attachment(filepath):
    print(f"🚀 AI Agent Activated for: {os.path.basename(filepath)}")
    
    # 1. READ
    text = get_pdf_text(filepath)
    if not text: return

    # 2. THINK (Invoke LangGraph)
    result = agent_app.invoke({"invoice_text": text, "retry_count": 0})
    decision = result['final_decision']
    reasons = result.get('analysis_notes', [])
    
    # 3. ACT
    if decision == "PAY":
        print(f"✅ APPROVED. Scheduling Payment...")
        data = result.get("extracted_data") 
        
        if data:
            payment_result = process_payment(
                amount=data.total_amount,
                currency=data.currency,
                vendor_name=data.vendor_name,
                invoice_ref=data.po_number or "No-PO"
            )
            
            if payment_result["status"] == "success":
                print(f"💰 PAYMENT SENT! ID: {payment_result['transfer_id']}")
                log_to_ledger(
                    vendor_name=data.vendor_name,
                    amount=data.total_amount,
                    currency=data.currency,
                    invoice_ref=data.po_number or "No-PO",
                    transfer_id=payment_result['transfer_id']
                )
                move_file(filepath, PAID_DIR)
                print(f"📂 Moved to: {PAID_DIR}")
            else:
                print(f"⚠️ Payment Failed: {payment_result.get('error')}")
                send_slack_payment_error(os.path.basename(filepath), payment_result.get('error'))
                move_file(filepath, FAILED_PAY_DIR)
                print(f"📂 Moved to FAILED folder: {FAILED_PAY_DIR}")


    elif decision in ["FLAG", "REJECTED"]: 
        print(f"⚠️ Action Required: {decision}")
        
        # Prepare the detail string for Slack
        reason_text = ", ".join(reasons) if reasons else "Unknown anomaly"
        
        # --- SEND THE SLACK ALERT ---
        send_slack_alert(
            filename=os.path.basename(filepath),
            reason=decision,
            details=reason_text
        )
        
        # Move to flagged folder for manual review
        move_file(filepath, FLAGGED_DIR)
        print(f"📂 Moved to: {FLAGGED_DIR}")


def check_email():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")

        # Search for unread emails containing attachments
        status, messages = mail.search(None, "UNSEEN")
        email_ids = messages[0].split()

        if email_ids:
            print(f"\n📧 Processing {len(email_ids)} new emails...")

        for email_id in email_ids:
            res, msg = mail.fetch(email_id, "(RFC822)")
            for response in msg:
                if isinstance(response, tuple):
                    msg = email.message_from_bytes(response[1])
                    subject = decode_header(msg["Subject"])[0][0]
                    if isinstance(subject, bytes): subject = subject.decode()
                    
                    print(f"   Subject: {subject}")

                    # Find PDF attachment
                    found_pdf = False
                    for part in msg.walk():
                        if part.get_content_maintype() == "multipart": continue
                        if part.get("Content-Disposition") is None: continue
                        
                        filename = part.get_filename()
                        if filename and filename.endswith(".pdf"):
                            found_pdf = True
                            filepath = os.path.join(INPUT_DIR, filename)
                            with open(filepath, "wb") as f:
                                f.write(part.get_payload(decode=True))
                            
                            process_attachment(filepath)
                    
                    if not found_pdf:
                        print("   (No PDF found in this email)")

        mail.logout()
    except Exception as e:
        print(f"⚠️ Error checking email: {e}")


if __name__ == "__main__":
    print(f"📡 Monitoring {EMAIL_USER} for Invoices...")
    print("   (Press Ctrl+C to stop)")
    
    while True:
        check_email()
        time.sleep(5) 