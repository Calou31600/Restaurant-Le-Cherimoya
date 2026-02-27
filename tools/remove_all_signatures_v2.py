import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")

headers = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

def get_all_menu_items():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Dynamic_Menu"
    records = []
    offset = None
    while True:
        params = {}
        if offset:
            params['offset'] = offset
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            records.extend(data.get('records', []))
            offset = data.get('offset')
            if not offset:
                break
        else:
            print(f"Error fetching records: {response.text}")
            break
    return records

def remove_signature(record_id):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Dynamic_Menu/{record_id}"
    data = {"fields": {"is_featured": False}}
    # On ajoute try/except et on catch tout
    try:
        response = requests.patch(url, headers=headers, json=data)
        if response.status_code == 200:
            return True
        print(f"Failed to update {record_id}: {response.text}")
        return False
    except Exception as e:
        print(f"Exception during update {record_id}: {e}")
        return False

if __name__ == "__main__":
    print("Fetching all records...")
    records = get_all_menu_items()
    print(f"Trouvé {len(records)} plats. Vérification des statuts 'is_featured'...")
    
    count = 0
    for record in records:
        fields = record.get("fields", {})
        # Vérifier si is_featured est vrai ou présent
        if fields.get("is_featured"):
            print(f"-> Désactivation de : {fields.get('Plat', 'Plat inconnu')} (ID: {record['id']})")
            success = remove_signature(record['id'])
            if success:
                count += 1
                
    print(f"Terminé. {count} plats ont été officiellement retirés des signatures.")
