# 🤖 AI Accounts Payable Agent

An autonomous invoice processing system powered by **LangGraph** and **Google Gemini**. It reads PDF invoices, validates them against a database of vendors and purchase orders, auto-pays approved invoices via **Stripe**, and alerts your team on **Slack** when something looks wrong.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| **AI Extraction** | Uses Google Gemini to parse PDF invoices into structured data (vendor, amount, PO#, line items) |
| **5-Rule Validation** | Fuzzy vendor matching, PO existence, price comparison, line item verification, auto-pay limits |
| **Auto-Payment** | Approved invoices are paid instantly via Stripe |
| **Slack Alerts** | Flagged or rejected invoices trigger real-time Slack notifications |
| **Accounting Sync** | Every payment is logged to a CSV general ledger with GL codes |
| **Email Monitoring** | Watches a Gmail inbox for incoming PDF invoices and processes them automatically |
| **Streamlit UI** | Web dashboard for manual invoice upload and review |

---

## 🏗️ Architecture

```
Email Inbox ──► email_listener.py ──► PDF saved to /invoices_input
                                          │
Streamlit UI ──► app.py ──────────────────┤
                                          ▼
                                   ┌─────────────┐
                                   │  agent.py    │  (LangGraph Workflow)
                                   │  ┌─────────┐ │
                                   │  │ Extract  │ │  ← extractor.py (Gemini AI)
                                   │  └────┬────┘ │
                                   │       ▼      │
                                   │  ┌─────────┐ │
                                   │  │Validate │ │  ← validator.py (SQLite rules)
                                   │  └────┬────┘ │
                                   │       ▼      │
                                   │  ┌─────────┐ │
                                   │  │ Decide  │ │  → PAY / REJECTED / FLAG
                                   │  └─────────┘ │
                                   └──────┬───────┘
                                          │
                        ┌─────────────────┼─────────────────┐
                        ▼                 ▼                 ▼
                   ✅ PAY            ⚠️ FLAG           ❌ REJECTED
                      │                 │                   │
             payment_manager.py    Slack Alert         Slack Alert
              (Stripe Payment)         │                   │
                      │                ▼                   ▼
            accounting_sync.py    /processed/flagged  /processed/flagged
             (CSV Ledger Log)
                      │
                 /processed/paid
```

---

## � Project Structure

```
Accounts_Payable/
├── agent.py               # LangGraph workflow (Extract → Validate → Decide)
├── extractor.py            # Gemini-powered PDF text → structured data
├── validator.py            # 5-rule validation against SQLite database
├── payment_manager.py      # Stripe payment processing
├── accounting_sync.py      # CSV general ledger logging
├── email_listener.py       # Gmail IMAP listener (auto-processes attachments)
├── app.py                  # Streamlit web UI for manual uploads
├── setup_db.py             # Database schema creation & seed data
├── graph.py                # Utility to export agent architecture as PNG
├── createpdf.py            # Utility to generate test invoice PDFs
├── .env.example            # Template for environment variables
├── .gitignore
├── invoices_input/         # Incoming invoices land here
└── processed/
    ├── paid/               # Successfully paid invoices
    ├── flagged/            # Invoices needing human review
    └── failed_payments/    # Payment gateway errors
```

---

## 🚀 Getting Started

### 1. Clone & Install

```bash
git clone https://github.com/Luckman-Khan/Accounts-Payable.git
cd Accounts-Payable

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your keys:

```env
GEMINI_API_KEY=your_gemini_api_key
STRIPE_SECRET_KEY=sk_test_...
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_gmail_app_password
MAX_AUTO_PAY_LIMIT=1000.0
```

> [!IMPORTANT]
> For Gmail, you must use an [App Password](https://support.google.com/accounts/answer/185833), not your regular password. Enable 2FA first, then generate an App Password.

### 3. Initialize the Database

```bash
python setup_db.py
```

This creates `ap_database.db` with sample vendors and purchase orders for testing.

---

## 🎮 Usage

### Option A: Email Listener (Autonomous Mode)

Monitors your inbox and auto-processes any PDF attachments:

```bash
python email_listener.py
```

The agent will continuously poll for new emails every 5 seconds. When a PDF invoice arrives:

1. Extracts text from the PDF
2. Sends it through the LangGraph agent pipeline
3. **Approved** → Pays via Stripe, logs to ledger, moves to `processed/paid/`
4. **Rejected/Flagged** → Sends Slack alert, moves to `processed/flagged/`

### Option B: Streamlit UI (Manual Mode)

Upload invoices manually through a web interface:

```bash
streamlit run app.py
```

---

## ⚙️ Validation Rules

The agent validates every invoice against 5 rules before making a decision:

| # | Rule | What It Checks |
|---|---|---|
| 1 | **Vendor Match** | Fuzzy-matches vendor name against the database (≥85% threshold) |
| 2 | **PO Existence** | Verifies the PO number exists in the system |
| 3 | **Price Check** | Compares invoice total vs PO amount (tolerance: $1.00) |
| 4 | **Line Item Match** | Checks invoice items against PO description using keyword matching |
| 5 | **Auto-Pay Limit** | Blocks auto-payment if amount exceeds `MAX_AUTO_PAY_LIMIT` |

---

## 🧪 Test Invoices

Use `createpdf.py` to generate test PDFs, or use the included samples:

| File | Scenario | Expected Result |
|---|---|---|
| `invoice_good.pdf` | Valid invoice matching PO-001 | ✅ PAY |
| `invoice_anomaly.pdf` | Inflated price ($9000 vs $5000 PO) | ❌ REJECTED |
| `invoice_bad_price.pdf` | Price mismatch | ❌ REJECTED |
| `invoice_fraud.pdf` | Unknown vendor or invalid PO | ❌ REJECTED |

---

## 🛠️ Tech Stack

- **AI/LLM** — Google Gemini (via LangChain)
- **Agent Framework** — LangGraph
- **Data Validation** — Pydantic + TheFuzz
- **Payments** — Stripe API
- **Database** — SQLite
- **Email** — IMAP (Gmail)
- **Alerts** — Slack Webhooks
- **Web UI** — Streamlit
- **PDF Parsing** — PyPDF

---

## 📄 License

This project is for educational and demonstration purposes.
