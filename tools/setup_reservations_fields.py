
import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_ID = "tblfoTW4toepkS4ez" # ID de la table Reservations
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

def add_fields():
    url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables/{TABLE_ID}/fields"
    
    fields_to_add = [
        {"name": "Telephone", "type": "phoneNumber"},
        {"name": "Date", "type": "date", "options": {"format": "YYYY-MM-DD"}},
        {"name": "Heure", "type": "singleLineText"},
        {"name": "Service", "type": "singleSelect", "options": {
            "choices": [{"name": "Midi"}, {"name": "Soir"}]
        }},
        {"name": "Couverts", "type": "number", "options": {"precision": 0}},
        {"name": "Statut", "type": "singleSelect", "options": {
            "choices": [{"name": "À confirmer"}, {"name": "Confirmée"}, {"name": "Annulée"}]
        }},
        {"name": "Notes", "type": "multilineText"}
    ]
    
    for field in fields_to_add:
        res = requests.post(url, headers=HEADERS, json=field)
        if res.status_code == 200:
            print(f"Champ '{field['name']}' ajouté.")
        else:
            print(f"Erreur champ '{field['name']}': {res.status_code} - {res.text}")

if __name__ == "__main__":
    add_fields()
