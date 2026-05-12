import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
HEADERS = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
BASE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Dynamic_Menu"

RECORDS_TO_CHECK = [
    "recBK9Gai9eQqTfE3", # Tataki de Saumon
    "recczq7vid7NwRgNI", # Bœuf Sauté
    "recwsP7GLzVt7LTrF", # Bœuf Vermicelles
    "recmvqJp5ONJoLOLA", # Joue de bœuf
]

for rid in RECORDS_TO_CHECK:
    res = requests.get(f"{BASE_URL}/{rid}", headers=HEADERS)
    data = res.json()
    fields = data.get("fields", {})
    print(f"Plat: {fields.get('Plat')} | Photo: {fields.get('Photo')}")
