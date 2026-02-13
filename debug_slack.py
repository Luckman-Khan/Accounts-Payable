import os
from dotenv import load_dotenv
import requests

# 1. Force load the .env file
print("📂 Loading .env file...")
loaded = load_dotenv()
print(f"✅ .env loaded? {loaded}")

# 2. Get the URL
webhook_url = os.getenv("SLACK_WEBHOOK_URL")

# 3. Debug Prints
if webhook_url:
    print(f"🔗 Found URL: {webhook_url[:10]}... (hidden)")
else:
    print("❌ ERROR: SLACK_WEBHOOK_URL variable is None or Empty.")
    print("👉 Check your .env file name and variable name.")
    exit()

# 4. Attempt to Send
print("🚀 Sending test message...")
payload = {"text": "🔔 This is a test from Python debug script."}

try:
    response = requests.post(webhook_url, json=payload)
    print(f"📡 Status Code: {response.status_code}")
    print(f"📝 Response Body: {response.text}")
    
    if response.status_code == 200:
        print("✅ SUCCESS! Check your Slack channel.")
    else:
        print("⚠️ FAILED. Slack rejected the request.")

except Exception as e:
    print(f"❌ CRITICAL ERROR: {e}")