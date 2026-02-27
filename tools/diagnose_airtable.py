
import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

def test_table(table_name):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table_name}?maxRecords=1"
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    print(f"Vérification de '{table_name}'...")
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            print(f"  ✅ OK")
        elif res.status_code == 403:
            print(f"  ❌ Accès Interdit (403) - Vérifie les scopes du Token.")
        elif res.status_code == 404:
            print(f"  ❓ Table introuvable (404) - Vérifie le nom exact (accents, etc.)")
        else:
            print(f"  ⚠️ Erreur {res.status_code}: {res.text}")
    except Exception as e:
        print(f"  💥 Erreur réseau: {e}")

if __name__ == "__main__":
    test_table("Dynamic_Menu")
    test_table("Reservations")
    test_table("Disponibilités")
