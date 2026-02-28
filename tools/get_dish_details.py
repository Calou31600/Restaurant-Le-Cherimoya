import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
HEADERS = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
BASE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Dynamic_Menu"

def get_all():
    records = []
    url = BASE_URL
    while True:
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        if "records" in data:
            records.extend(data["records"])
        if "offset" in data:
            url = f"{BASE_URL}?offset={data['offset']}"
        else:
            break
    return records

records = get_all()
summary = []
for r in records:
    fields = r['fields']
    summary.append({
        "id": r['id'],
        "plat": fields.get('Plat', 'N/A'),
        "description": fields.get('description_geo', 'N/A'),
        "has_photo": "Photo" in fields and len(fields["Photo"]) > 0
    })

with open('dishes.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(f"Total records: {len(records)} written to dishes.json")
