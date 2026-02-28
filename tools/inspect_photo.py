import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
HEADERS = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

def check_first_photo():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Dynamic_Menu"
    res = requests.get(url, headers=HEADERS)
    records = res.json().get("records", [])
    for r in records:
        fields = r.get("fields", {})
        if "Photo" in fields:
            print(f"Type of Photo for {fields.get('Plat')}: {type(fields['Photo'])}")
            print(f"Value: {json.dumps(fields['Photo'], indent=2)}")
            break

if __name__ == "__main__":
    check_first_photo()
