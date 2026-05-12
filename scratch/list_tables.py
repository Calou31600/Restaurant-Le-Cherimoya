import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
HEADERS = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

def list_tables():
    url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
    res = requests.get(url, headers=HEADERS)
    return res.json().get("tables", [])

if __name__ == "__main__":
    tables = list_tables()
    print("Tables dans la base :")
    for t in tables:
        print(f"- {t['name']} ({t['id']})")
