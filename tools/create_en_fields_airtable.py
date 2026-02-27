import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("AIRTABLE_API_KEY")
base_id = os.environ.get("AIRTABLE_BASE_ID")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

try:
    print("Récupération de l'ID de la table Dynamic_Menu...")
    res = requests.get(f"https://api.airtable.com/v0/meta/bases/{base_id}/tables", headers=headers)
    
    if res.status_code != 200:
        print(f"Erreur d'accès à l'API Metadata: {res.status_code}")
        exit(1)
        
    data = res.json()
    table_id = None
    for table in data.get("tables", []):
        if table["name"] == "Dynamic_Menu":
            table_id = table["id"]
            break
            
    if not table_id:
        print("Table Dynamic_Menu introuvable.")
        exit(1)
    
    # Création du champ Plat_EN
    print("Création du champ 'Plat_EN'...")
    res_plat = requests.post(
        f"https://api.airtable.com/v0/meta/bases/{base_id}/tables/{table_id}/fields",
        headers=headers,
        json={"name": "Plat_EN", "type": "singleLineText"}
    )
    if res_plat.status_code == 200:
        print("✅ Champ 'Plat_EN' créé.")
    else:
        print(f"Champ Plat_EN déjà existant ou erreur: {res_plat.text}")

    # Création du champ description_geo_EN
    print("Création du champ 'description_geo_EN'...")
    res_desc = requests.post(
        f"https://api.airtable.com/v0/meta/bases/{base_id}/tables/{table_id}/fields",
        headers=headers,
        json={"name": "description_geo_EN", "type": "multilineText"}
    )
    if res_desc.status_code == 200:
        print("✅ Champ 'description_geo_EN' créé.")
    else:
        print(f"Champ description_geo_EN déjà existant ou erreur: {res_desc.text}")

except Exception as e:
    print(f"Exception : {e}")
