
import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

def create_minimal_dispo():
    url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
    payload = {
        "name": "Disponibilites",
        "description": "Inventaire",
        "fields": [
            {"name": "Date", "type": "date", "options": {"dateFormat": {"name": "iso", "format": "YYYY-MM-DD"}}},
            {"name": "Service", "type": "singleSelect", "options": {"choices": [{"name": "Midi"}, {"name": "Soir"}]}},
            {"name": "Capacite totale", "type": "number", "options": {"precision": 0}},
            {"name": "Reservations confirmees", "type": "number", "options": {"precision": 0}},
            {"name": "Statut", "type": "singleSelect", "options": {"choices": [{"name": "Ouvert"}, {"name": "Complet"}]}}
        ]
    }
    res = requests.post(url, headers=HEADERS, json=payload)
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text}")

if __name__ == "__main__":
    create_minimal_dispo()
