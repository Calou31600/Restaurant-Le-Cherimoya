
import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = "Reservations"

def check_tables():
    tables = ["Reservations", "Disponibilités"]
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    
    for table in tables:
        print(f"Vérification de la table '{table}'...")
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table}?maxRecords=1"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                print(f"✅ La table '{table}' existe.")
                data = response.json()
                records = data.get("records", [])
                if records:
                    print(f"   Champs détectés : {list(records[0].get('fields', {}).keys())}")
                else:
                    print("   La table est vide.")
            elif response.status_code == 404:
                print(f"❌ La table '{table}' n'existe pas.")
            else:
                print(f"⚠️ Erreur ({response.status_code}) : {response.text}")
        except Exception as e:
            print(f"❌ Erreur réseau : {e}")

if __name__ == "__main__":
    check_tables()
