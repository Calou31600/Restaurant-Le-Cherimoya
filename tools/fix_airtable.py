import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")

headers = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

# 1. Get the Tables
meta_url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
response = requests.get(meta_url, headers=headers)

if response.status_code != 200:
    print(f"Error getting meta: {response.text}")
    exit(1)

tables = response.json().get('tables', [])
dynamic_menu_table = next((t for t in tables if t['name'] == 'Dynamic_Menu'), None)

if not dynamic_menu_table:
    print("Table Dynamic_Menu not found.")
    exit(1)

table_id = dynamic_menu_table['id']

# 2. Check fields for "Menu"
menu_field = next((f for f in dynamic_menu_table['fields'] if f['name'] == 'Menu'), None)

payload = {
    "name": "Menu",
    "type": "multipleSelects",
    "options": {
        "choices": [
            {"name": "À Partager"},
            {"name": "Entrées"},
            {"name": "Côté Terre"},
            {"name": "Côté Mer"},
            {"name": "Formules"},
            {"name": "Douceurs"},
            {"name": "Boissons"}
        ]
    }
}

if menu_field:
    print(f"Field 'Menu' exists with type: {menu_field['type']}. Updating...")
    field_id = menu_field['id']
    update_url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables/{table_id}/fields/{field_id}"
    res = requests.patch(update_url, headers=headers, json=payload)
    print(res.status_code)
    print(res.text)
else:
    print("Field 'Menu' does not exist. Creating...")
    create_url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables/{table_id}/fields"
    res = requests.post(create_url, headers=headers, json=payload)
    print(res.status_code)
    print(res.text)
