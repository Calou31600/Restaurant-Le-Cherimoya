
import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

def list_tables():
    url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    print(f"Base: {AIRTABLE_BASE_ID}")
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            tables = res.json().get("tables", [])
            print(f"Tables trouvées ({len(tables)}):")
            for t in tables:
                print(f"- {t['name']}")
        else:
            print(f"Error {res.status_code}: {res.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_tables()
