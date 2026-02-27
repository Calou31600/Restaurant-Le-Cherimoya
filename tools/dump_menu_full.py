import os
import requests
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
print(f"Total records in Airtable: {len(records)}")
for i, r in enumerate(records):
    print(f"{i+1}. {r['fields'].get('Plat')}")
