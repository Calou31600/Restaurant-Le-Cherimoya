import os
import requests
from dotenv import load_dotenv

load_dotenv()
AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")

url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Dynamic_Menu"
headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

response = requests.get(url, headers=headers)
data = response.json()

all_categories = set()
for r in data.get('records', []):
    cats = r.get('fields', {}).get('Menu', [])
    for c in cats:
        all_categories.add(c)

print("Catégories actuellement lues depuis Airtable:")
for c in sorted(list(all_categories)):
    print(f"- '{c}'")
