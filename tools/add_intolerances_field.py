import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
HEADERS = {"Authorization": f"Bearer {AIRTABLE_API_KEY}", "Content-Type": "application/json"}

def get_table_name():
    # Parfois c'est "Dynamic_Menu" ou l'ID de la table
    url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        for table in res.json().get("tables", []):
            if table.get("name") == "Dynamic_Menu":
                return table.get("id")
    return None

def create_intolerances_field():
    table_id = get_table_name()
    if not table_id:
        print("Table Dynamic_Menu non trouvée.")
        return

    url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables/{table_id}/fields"
    payload = {
        "name": "intolerances",
        "description": "Liste des intolérances: Lactose, Gluten, Cacahuète",
        "type": "multipleSelects",
        "options": {
            "choices": [
                {"name": "Lactose"},
                {"name": "Gluten"},
                {"name": "Cacahuète"}
            ]
        }
    }
    
    res = requests.post(url, headers=HEADERS, json=payload)
    if res.status_code in [200, 201]:
        print("Champ 'intolerances' créé avec succès.")
    else:
        print(f"Erreur création champ: {res.status_code} - {res.text}")

        # Check if field already exists by getting the table schema
        url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables/{table_id}"
        res2 = requests.get(url, headers=HEADERS)
        if res2.status_code == 200:
            for field in res2.json().get("fields", []):
                if field.get("name") == "intolerances":
                    print("Le champ 'intolerances' existait déjà.")

if __name__ == "__main__":
    create_intolerances_field()
