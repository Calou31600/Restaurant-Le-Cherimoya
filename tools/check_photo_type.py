import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
HEADERS = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

def check_photo_field():
    url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
    res = requests.get(url, headers=HEADERS)
    data = res.json()
    for table in data.get("tables", []):
        if table.get("name") == "Dynamic_Menu":
            for field in table.get("fields", []):
                if field['name'] == 'Photo':
                    print(f"PHOTO_TYPE: {field['type']}")
                    if field['type'] in ['lookup', 'rollup', 'formula']:
                        print("WARNING: This is a read-only field!")
                    
if __name__ == "__main__":
    check_photo_field()
