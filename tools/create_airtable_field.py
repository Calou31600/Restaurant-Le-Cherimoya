import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

api_key = os.environ.get("AIRTABLE_API_KEY")
base_id = os.environ.get("AIRTABLE_BASE_ID")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# 1. Obtenir les tables pour trouver l'ID de la table Dynamic_Menu
try:
    print("Récupération du schéma de la base...")
    res = requests.get(f"https://api.airtable.com/v0/meta/bases/{base_id}/tables", headers=headers)
    
    if res.status_code != 200:
        print(f"Erreur d'accès à l'API Metadata: {res.status_code}")
        print(res.text)
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
        
    print(f"ID de la table Dynamic_Menu : {table_id}")
    
    # 2. Créer le champ Photo
    print("Création du champ 'Photo' de type 'multipleAttachments'...")
    field_payload = {
        "name": "Photo",
        "type": "multipleAttachments"
    }
    
    res_field = requests.post(
        f"https://api.airtable.com/v0/meta/bases/{base_id}/tables/{table_id}/fields",
        headers=headers,
        json=field_payload
    )
    
    if res_field.status_code == 200:
        print("✅ Champ 'Photo' créé avec succès !")
    else:
        print(f"❌ Erreur lors de la création du champ : {res_field.status_code}")
        print(res_field.text)

except Exception as e:
    print(f"Exception : {e}")
