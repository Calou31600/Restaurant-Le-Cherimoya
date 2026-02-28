
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

def create_clients_table():
    url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
    
    table_data = {
        "name": "Clients",
        "description": "Base de données clients du Chérimoya",
        "fields": [
            {"name": "Nom", "type": "singleLineText"}
        ]
    }
    
    res = requests.post(url, headers=HEADERS, json=table_data)
    if res.status_code == 200:
        print("Table 'Clients' créée avec succès !")
    else:
        print(f"Erreur: {res.status_code} - {res.text}")

if __name__ == "__main__":
    create_clients_table()
