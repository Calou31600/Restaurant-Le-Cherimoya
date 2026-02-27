
import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = "Dynamic_Menu"
HEADERS = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

def audit():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME}"
    all_records = []
    offset = None
    while True:
        params = {"offset": offset} if offset else {}
        res = requests.get(url, headers=HEADERS, params=params)
        data = res.json()
        all_records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
            
    print(f"Total des records dans Airtable: {len(all_records)}")
    
    categories = {}
    for r in all_records:
        fields = r.get("fields", {})
        plat = fields.get("Plat")
        menus = fields.get("Menu", [])
        for m in menus:
            categories[m] = categories.get(m, 0) + 1
            
    print("Détails par catégorie (Airtable):")
    for cat, count in categories.items():
        print(f"- {cat}: {count}")
        
    # Check for missing categories
    no_cat = [r.get("fields", {}).get("Plat") for r in all_records if not r.get("fields", {}).get("Menu")]
    if no_cat:
        print(f"Plats sans catégorie: {len(no_cat)}")
        for p in no_cat:
            print(f"  - {p}")

if __name__ == "__main__":
    audit()
