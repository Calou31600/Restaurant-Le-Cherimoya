import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
HEADERS = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

def inspect_all_fields():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Dynamic_Menu"
    res = requests.get(url, headers=HEADERS)
    records = res.json().get("records", [])
    if records:
        with open('fields_dump.json', 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    inspect_all_fields()
