
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

def create_reservations_table():
    url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
    
    table_data = {
        "name": "Reservations",
        "description": "Table pour stocker les demandes de réservation du site web",
        "fields": [
            {"name": "Nom", "type": "singleLineText"},
            {"name": "Telephone", "type": "phoneNumber"},
            {"name": "Date", "type": "date", "options": {"format": "YYYY-MM-DD"}},
            {"name": "Heure", "type": "singleLineText"},
            {"name": "Service", "type": "singleSelect", "options": {
                "choices": [
                    {"name": "Midi"},
                    {"name": "Soir"}
                ]
            }},
            {"name": "Couverts", "type": "number", "options": {"precision": 0}},
            {"name": "Statut", "type": "singleSelect", "options": {
                "choices": [
                    {"name": "À confirmer"},
                    {"name": "Confirmée"},
                    {"name": "Annulée"}
                ]
            }},
            {"name": "Notes", "type": "multilineText"}
        ]
    }
    
    res = requests.post(url, headers=HEADERS, json=table_data)
    if res.status_code == 200:
        print("Table 'Reservations' créée avec succès !")
    elif res.status_code == 422:
        print("La table 'Reservations' existe déjà ou erreur de schéma.")
    else:
        print(f"Erreur: {res.status_code} - {res.text}")

if __name__ == "__main__":
    create_reservations_table()
