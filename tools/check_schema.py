
import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
HEADERS = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

def check_schema():
    url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
    res = requests.get(url, headers=HEADERS)
    if res.status_code != 200:
        print(f"Error: {res.status_code} - {res.text}")
        return
        
    data = res.json()
    for table in data.get("tables", []):
        if table.get("name") == "Dynamic_Menu":
            print(f"Table Found: {table.get('name')}")
            for field in table.get("fields", []):
                if field.get("name") == "Menu":
                    print(f"Field Found: {field.get('name')}")
                    choices = field.get("options", {}).get("choices", [])
                    print("Allowed Choices:")
                    for choice in choices:
                        print(f"  - '{choice.get('name')}'")

if __name__ == "__main__":
    check_schema()
