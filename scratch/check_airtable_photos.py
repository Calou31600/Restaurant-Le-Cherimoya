import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

api_key = os.getenv('AIRTABLE_API_KEY')
base_id = os.getenv('AIRTABLE_BASE_ID')
headers = {"Authorization": f"Bearer {api_key}"}

def get_menu():
    url = f"https://api.airtable.com/v0/{base_id}/Dynamic_Menu"
    records = []
    offset = None
    
    while True:
        params = {}
        if offset:
            params['offset'] = offset
        
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        records.extend(data.get('records', []))
        
        offset = data.get('offset')
        if not offset:
            break
            
    return records

if __name__ == "__main__":
    menu = get_menu()
    missing = []
    for r in menu:
        fields = r.get('fields', {})
        if not fields.get('Photo'):
            missing.append({
                "id": r['id'],
                "plat": fields.get('Plat'),
                "desc": fields.get('description_geo') or fields.get('Description')
            })
    
    with open('current_missing_photos.json', 'w', encoding='utf-8') as f:
        json.dump(missing, f, indent=2, ensure_ascii=False)
    
    print(f"Trouvé {len(missing)} plats sans photos.")
