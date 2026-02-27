
import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

def final_diagnosis():
    tables = ["Dynamic_Menu", "Reservations", "Disponibilites"]
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    
    print(f"Base: {AIRTABLE_BASE_ID}")
    
    for table in tables:
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table}?maxRecords=1"
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            count = len(res.json().get('records', []))
            print(f"✅ {table}: OK ({count} records found)")
        else:
            print(f"❌ {table}: Erreur {res.status_code}")

if __name__ == "__main__":
    final_diagnosis()
