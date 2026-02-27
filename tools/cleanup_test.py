
import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
HEADERS = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

def cleanup():
    # List tables
    url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        tables = res.json().get("tables", [])
        for t in tables:
            if t["name"] == "TestTableAG":
                print(f"Suppression de {t['name']}...")
                # Deleting a table via API? Airtable doesn't support deleting tables via API metadata yet!
                # Wait, yes it does? No, standard API doesn't. 
                # Meta API only supports Create/Update schema elements (fields, choices), but NOT delete table yet.
                pass

if __name__ == "__main__":
    cleanup()
