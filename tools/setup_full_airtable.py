
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

def create_table(table_data):
    url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
    print(f"Création de la table '{table_data['name']}'...")
    res = requests.post(url, headers=HEADERS, json=table_data)
    if res.status_code == 200:
        print(f"✅ Table '{table_data['name']}' créée avec succès !")
    else:
        print(f"❌ Erreur {res.status_code} sur '{table_data['name']}': {res.text}")

def setup():
    # Schema pour Reservations
    reservations_schema = {
        "name": "Reservations",
        "description": "Table des réservations clients",
        "fields": [
            {"name": "Nom", "type": "singleLineText"},
            {"name": "Email", "type": "email"},
            {"name": "Telephone", "type": "phoneNumber"},
            {"name": "Date", "type": "date", "options": {"format": "YYYY-MM-DD"}},
            {"name": "Heure", "type": "singleLineText"},
            {"name": "Service", "type": "singleSelect", "options": {
                "choices": [{"name": "Midi"}, {"name": "Soir"}]
            }},
            {"name": "Couverts", "type": "number", "options": {"format": "decimal", "precision": 0}},
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

    # Schema pour Disponibilités (Inventory)
    dispo_schema = {
        "name": "Disponibilites",
        "description": "Gestion de l'inventaire des places par service",
        "fields": [
            {"name": "Date", "type": "date", "options": {"format": "YYYY-MM-DD"}},
            {"name": "Service", "type": "singleSelect", "options": {
                "choices": [{"name": "Midi"}, {"name": "Soir"}]
            }},
            {"name": "Capacite totale", "type": "number", "options": {"format": "decimal", "precision": 0}},
            {"name": "Reservations confirmees", "type": "number", "options": {"format": "decimal", "precision": 0}},
            {"name": "Statut", "type": "singleSelect", "options": {
                "choices": [
                    {"name": "Ouvert"},
                    {"name": "Complet"},
                    {"name": "Restreint"}
                ]
            }}
        ]
    }

    create_table(reservations_schema)
    create_table(dispo_schema)

if __name__ == "__main__":
    if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
        print("❌ Erreur : AIRTABLE_API_KEY ou AIRTABLE_BASE_ID manquant.")
    else:
        setup()
