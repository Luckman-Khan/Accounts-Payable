import stripe
import os
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def normalize_currency(currency_input):
    """
    Converts symbols like '$' or '₹' into codes like 'usd' or 'inr'.
    """
    mapping = {
        "$": "usd",
        "USD": "usd",
        "₹": "inr",
        "INR": "inr",
        "€": "eur",
        "EUR": "eur",
        "£": "gbp",
        "GBP": "gbp"
    }
    # Clean the input: uppercase it and strip whitespace
    clean_input = str(currency_input).strip()
    return mapping.get(clean_input, "usd") # Default to 'usd' if unknown

def process_payment(amount, currency, vendor_name, invoice_ref):
    try:
        # 1. NORMALIZE THE CURRENCY (Fixes the '$' error)
        stripe_currency = normalize_currency(currency)
        
        # 2. Convert to cents
        amount_cents = int(amount * 100)
        
        print(f"💸 Processing Payment of ${amount} {stripe_currency.upper()} for {vendor_name}...")
        
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency=stripe_currency,
            description=f"Invoice Payment: {invoice_ref} to {vendor_name}",
            metadata={
                "vendor": vendor_name, 
                "po_number": invoice_ref,
                "status": "Auto-Approved"
            },
            payment_method="pm_card_visa", 
            confirm=True, 
            automatic_payment_methods={'enabled': True, 'allow_redirects': 'never'}
        )
        
        return {
            "status": "success", 
            "transfer_id": intent.id, 
            "receipt_url": f"https://dashboard.stripe.com/test/payments/{intent.id}"
        }

    except Exception as e:
        return {"status": "failed", "error": str(e)}