
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

def add_review_fields():
    # 1. Get Table ID for 'Clients'
    res = requests.get(f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables", headers=HEADERS)
    tables = res.json().get("tables", [])
    table_id = next((t["id"] for t in tables if t["name"] == "Clients"), None)
    
    if not table_id:
        print("Table 'Clients' introuvable.")
        return

    fields_to_add = [
        {"name": "Avis_Recu", "type": "checkbox", "options": {"icon": "check", "color": "greenBright"}},
        {"name": "Note", "type": "number", "options": {"precision": 0}}
    ]

    for field in fields_to_add:
        print(f"Ajout du champ '{field['name']}'...")
        res_field = requests.post(
            f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables/{table_id}/fields",
            headers=HEADERS,
            json=field
        )
        if res_field.status_code == 200:
            print(f"✅ Champ '{field['name']}' ajouté.")
        else:
            print(f"❌ Erreur pour '{field['name']}': {res_field.status_code} - {res_field.text}")

if __name__ == "__main__":
    add_review_fields()
