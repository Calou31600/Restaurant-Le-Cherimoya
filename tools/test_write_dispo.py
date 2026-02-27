
import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

def test_write_dispo():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Disponibilités"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "records": [
            {
                "fields": {
                    "Date": "2026-12-31",
                    "Service": "Soir",
                    "Capacité totale": 50,
                    "Réservations confirmées": 0,
                    "Statut": "Ouvert"
                }
            }
        ],
        "typecast": True
    }
    print(f"Test d'écriture dans 'Disponibilités'...")
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code == 200:
        print("✅ Écriture réussie !")
        record_id = res.json()["records"][0]["id"]
        requests.delete(f"{url}/{record_id}", headers=headers)
    else:
        print(f"❌ Erreur {res.status_code}: {res.text}")

if __name__ == "__main__":
    test_write_dispo()
