import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
HEADERS = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

def check_schema():
    url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
    res = requests.get(url, headers=HEADERS)
    data = res.json()
    for table in data.get("tables", []):
        if table.get("name") == "Dynamic_Menu":
            for field in table.get("fields", []):
                print(f"FIELD_INFO: {field['name']} | TYPE: {field['type']}")

if __name__ == "__main__":
    check_schema()
