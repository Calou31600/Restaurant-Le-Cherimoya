import os
import json
import requests
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Config Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Config Airtable
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

def get_airtable_data(table_name):
    """Récupère les données d'Airtable ou du cache local si erreur 429."""
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table_name}"
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.json().get('records', [])
        else:
            print(f"Erreur Airtable {res.status_code} pour {table_name}. Tentative via cache local...")
    except Exception as e:
        print(f"Erreur connexion Airtable: {e}")

    # Fallback sur le cache local pour le menu si Airtable bloque
    if table_name == 'Dynamic_Menu' and os.path.exists('.tmp/airtable_cache.json'):
        with open('.tmp/airtable_cache.json', 'r', encoding='utf-8') as f:
            cache = json.load(f)
            return cache.get('menu', {}).get('data', [])
    
    return []

def migrate_menu():
    print("Migration du MENU...")
    records = get_airtable_data('Dynamic_Menu')
    for r in records:
        f = r.get('fields', {})
        
        # Nettoyage du prix
        prix_raw = str(f.get('prix', '0'))
        prix = 0.0
        try:
            prix = float(prix_raw.replace('€', '').replace(',', '.').strip())
        except: pass

        # Photo
        photo = ""
        if f.get('Photo'):
            if isinstance(f['Photo'], list) and len(f['Photo']) > 0:
                photo = f['Photo'][0].get('url', '')
            else:
                photo = str(f['Photo'])

        data = {
            "plat": f.get('Plat', 'Sans nom'),
            "description_geo": f.get('description_geo', ''),
            "prix": prix,
            "tags_meteo": f.get('tags_meteo', []),
            "producteur_local": f.get('producteur_local', ''),
            "is_featured": str(f.get('is_featured', '')).lower() == 'true',
            "photo": photo
        }
        supabase.table("menu").insert(data).execute()
    print(f"Plats migres.")

def migrate_wines():
    print("Migration des VINS...")
    records = get_airtable_data('Carte_Vins')
    for r in records:
        f = r.get('fields', {})
        
        photo = ""
        if f.get('Photo'):
            if isinstance(f['Photo'], list) and len(f['Photo']) > 0:
                photo = f['Photo'][0].get('url', '')
            else:
                photo = str(f['Photo'])

        data = {
            "nom": f.get('Nom', 'Inconnu'),
            "nom_en": f.get('Nom_EN', ''),
            "appellation": f.get('Appellation', ''),
            "millesime": str(f.get('Millesime', '')),
            "prix_verre": f.get('Prix_Verre', ''),
            "prix_bouteille": f.get('Prix_Bouteille', ''),
            "type": f.get('Type', ''),
            "description": f.get('Description', ''),
            "description_en": f.get('Description_EN', ''),
            "photo": photo
        }
        supabase.table("wines").insert(data).execute()
    print(f"Vins migres.")

def migrate_events():
    print("Migration des EVENEMENTS...")
    records = get_airtable_data('Special_Menus_Cherimoya')
    for r in records:
        f = r.get('fields', {})
        data = {
            "name": f.get('Name', 'Événement'),
            "theme": f.get('Theme', 'personnalise'),
            "start_date": f.get('Start_Date'),
            "end_date": f.get('End_Date'),
            "active": bool(f.get('Active', False)),
            "price": f.get('Price', ''),
            "subtitle": f.get('Subtitle', ''),
            "entrees": f.get('Entrees', ''),
            "plats": f.get('Plats', ''),
            "desserts": f.get('Desserts', ''),
            "photo": f.get('Photo', '')
        }
        supabase.table("special_menus").insert(data).execute()
    print(f"Evenements migres.")

if __name__ == "__main__":
    print("Demarrage de la migration globale...")
    try:
        migrate_menu()
        migrate_wines()
        migrate_events()
        print("Migration terminee avec succes !")
    except Exception as e:
        print(f"Erreur pendant la migration: {e}")
