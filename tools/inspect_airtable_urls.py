import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('AIRTABLE_API_KEY')
base_id = os.getenv('AIRTABLE_BASE_ID')
table_name = "Dynamic_Menu"

headers = {"Authorization": f"Bearer {api_key}"}
url = f"https://api.airtable.com/v0/{base_id}/{table_name}"

def inspect_urls():
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        records = response.json().get('records', [])
        print(f"Total records: {len(records)}")
        import json
        for r in records[:10]:
            print(f"\n--- RECORD {r.get('id')} ---")
            print(json.dumps(r.get('fields', {}), indent=2, ensure_ascii=False))
    else:
        print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    inspect_urls()
