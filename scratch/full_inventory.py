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
    data = []
    for r in records:
        data.append({
            "id": r["id"],
            "plat": r["fields"].get("Plat"),
            "photo": r["fields"].get("Photo")
        })
    
    with open("full_menu_inventory.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Inventaire de {len(data)} plats sauvegardé dans full_menu_inventory.json")
