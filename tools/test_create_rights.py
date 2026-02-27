
import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

def test_create_dummy():
    url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
    payload = {
        "name": "TestTableAG",
        "fields": [{"name": "Name", "type": "singleLineText"}]
    }
    print("Tentative de création d'une table test...")
    res = requests.post(url, headers=HEADERS, json=payload)
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text}")

if __name__ == "__main__":
    test_create_dummy()
