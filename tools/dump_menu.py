import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
HEADERS = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Dynamic_Menu"

response = requests.get(url, headers=HEADERS)
data = response.json()
records = data.get('records', [])
print(f"Total records in Airtable: {len(records)}")
for r in records:
    print(f"- {r['fields'].get('Plat')}")
