import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
HEADERS = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
BASE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Dynamic_Menu"

def get_airtable_records():
    url = BASE_URL
    records = []
    offset = None
    while True:
        params = {}
        if offset:
            params['offset'] = offset
        res = requests.get(url, headers=HEADERS, params=params)
        data = res.json()
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    return records

if __name__ == "__main__":
    records = get_airtable_records()
    for r in records:
        plat = r['fields'].get('Plat')
        if plat and 'Siu' in plat:
            print(f"{r['id']} | {plat} | {repr(plat)}")
