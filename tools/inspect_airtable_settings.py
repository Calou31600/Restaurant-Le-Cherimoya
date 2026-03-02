import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def inspect_settings():
    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')
    table_name = "Settings_Cherimoya"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    print(f"Inspecting table: {table_name}")
    
    # Check Schema via Meta API
    meta_url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    meta_response = requests.get(meta_url, headers=headers)
    
    if meta_response.status_code == 200:
        tables = meta_response.json().get('tables', [])
        target_table = next((t for t in tables if t['name'] == table_name), None)
        if target_table:
            print("\n--- CLOSED DAYS FIELD ---")
            closed_days_field = next((f for f in target_table['fields'] if f['name'] == 'closedDays'), None)
            if closed_days_field:
                print(json.dumps(closed_days_field, indent=2))
            else:
                print("Field 'closedDays' not found.")
        else:
            print(f"Table {table_name} not found in Meta API.")
    else:
        print(f"Meta API Error: {meta_response.status_code}, {meta_response.text}")

    # Check Records
    data_url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    data_response = requests.get(data_url, headers=headers)
    
    if data_response.status_code == 200:
        records = data_response.json().get('records', [])
        print("\n--- RECORDS ---")
        print(json.dumps(records, indent=2))
    else:
        print(f"Data API Error: {data_response.status_code}, {data_response.text}")

if __name__ == "__main__":
    inspect_settings()
