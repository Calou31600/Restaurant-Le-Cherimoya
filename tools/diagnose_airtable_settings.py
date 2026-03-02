import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('AIRTABLE_API_KEY')
base_id = os.getenv('AIRTABLE_BASE_ID')
headers = {"Authorization": f"Bearer {api_key}"}

def check_settings_existence():
    # 1. Check data API
    url_data = f"https://api.airtable.com/v0/{base_id}/Settings"
    print(f"Checking data API: {url_data}")
    r_data = requests.get(url_data, headers=headers)
    print(f"Data API Response: {r_data.status_code}")
    if r_data.status_code != 200:
        print(f"Data API Error: {r_data.text}")
    else:
        print("Data API says: Table EXISTS and is accessible.")

    # 2. Check meta API
    url_meta = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    print(f"\nChecking meta API: {url_meta}")
    r_meta = requests.get(url_meta, headers=headers)
    print(f"Meta API Response: {r_meta.status_code}")
    if r_meta.status_code == 200:
        tables = r_meta.json().get('tables', [])
        names = [t['name'] for t in tables]
        print(f"Tables in base: {names}")
        if "Settings" in names:
            print("Meta API says: Table EXISTS in schema.")
        else:
            print("Meta API says: Table DOES NOT EXIST in schema.")
    else:
        print(f"Meta API Error: {r_meta.text}")

if __name__ == "__main__":
    check_settings_existence()
