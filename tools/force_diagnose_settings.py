import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('AIRTABLE_API_KEY')
base_id = os.getenv('AIRTABLE_BASE_ID')
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

def force_diagnose():
    print(f"DEBUG: Base ID = {base_id}")
    print(f"DEBUG: API Key length = {len(api_key)}")
    
    # List tables FIRST
    url_list = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    r_list = requests.get(url_list, headers=headers)
    print(f"List Tables Status: {r_list.status_code}")
    if r_list.status_code == 200:
        names = [t['name'] for t in r_list.json().get('tables', [])]
        print(f"Existing tables: {names}")
    else:
        print(f"List Tables Error: {r_list.text}")

    # Try to create table Settings
    table_schema = {
        "name": "Settings",
        "description": "Paramètres",
        "fields": [
            {"name": "totalSeats", "type": "number"}
        ]
    }
    print("\nAttempting to create table 'Settings'...")
    r_create = requests.post(url_list, json=table_schema, headers=headers)
    print(f"Create Table Status: {r_create.status_code}")
    print(f"Create Table Response: {r_create.text}")

if __name__ == "__main__":
    force_diagnose()
