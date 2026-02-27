
import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

def test_write_reservations():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Reservations"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "records": [
            {
                "fields": {
                    "Nom": "Test AG",
                    "Email": "test@example.com",
                    "Date": "2026-12-31",
                    "Heure": "20:00",
                    "Service": "Soir",
                    "Couverts": 2,
                    "Statut": "À confirmer"
                }
            }
        ],
        "typecast": True
    }
    print(f"Test d'écriture dans 'Reservations'...")
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code == 200:
        print("✅ Écriture réussie !")
        record_id = res.json()["records"][0]["id"]
        # Now try to delete it to keep it clean
        requests.delete(f"{url}/{record_id}", headers=headers)
    else:
        print(f"❌ Erreur {res.status_code}: {res.text}")

if __name__ == "__main__":
    test_write_reservations()
