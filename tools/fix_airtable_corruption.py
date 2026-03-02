import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Configuration
AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
HEADERS = {"Authorization": f"Bearer {AIRTABLE_API_KEY}", "Content-Type": "application/json"}
BASE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Dynamic_Menu"

DISHES_JSON = r"c:\Users\pasca\Downloads\Programme vibe coding\Restaurant Le Cherimoya\dishes.json"

# List of Cloudinary links generated in this session (extracted from mapping and logic)
# Note: I'll use the mapping logic to find which dishes need a Photo update
MAPPING = {
    "siu_mai_vapeur_5pc": "Siu mai vapeur 5pc",
    "filet_bar_beurre": "Filet de bar au beurre",
    "sunset_boulevard": "Sunset boulevard",
    "canard_caramel_balsamique": "Filet de canard sauce caramel balsamique",
    "salade_poulet_croustillant": "Salade de poulet croustillant",
    "assiette_fruits_mer": "Assiette de fruits de mer",
    "creme_brulee_cafe": "Crème Brûlée au Café",
    "nana_fizz": "Nana fizz",
    "plateau_fromages_mixtes": "Plateau de fromages mixtes",
    "salade_nems": "Salade de nems",
    "joue_boeuf_confite": "Joue de bœuf confite au four",
    "faux_filet_boeuf": "Faux filet de bœuf 250gr",
    "virgin_mojito": "Virgin mojito",
    "moules_creme_beurre": "Moules à la crème beurre",
    "ha_kao_crevettes": "Ha Kao aux crevettes 5 pc",
    "dome_rubis": "Dôme rubis",
    "gambas_grillees_3pc": "Grosses gambas grillées 3pc"
}

# Base Cloudinary folder if we need to reconstruct or check
# But better: just use the specific URLs if I have them or let the user know.
# Actually, I can just update the METADATA first (Plat, Description, Price) to stop the corruption.

def clean_data():
    with open(DISHES_JSON, 'r', encoding='utf-8') as f:
        dishes = json.load(f)
    
    print(f"Loaded {len(dishes)} dishes from dishes.json")
    
    for dish in dishes:
        record_id = dish['id']
        plat_name = dish['plat']
        description = dish['description']
        # Try to infer price if possible, or leave 0 for now to avoid string pollution
        # If I see a price in dishes.json I'll use it, but it seems it's not there.
        
        print(f"Fixing {record_id} ({plat_name})...")
        
        fields = {
            "Plat": plat_name,
            "description_geo": description,
            # Reset corrupted fields if they contain JSON markers
            # For prize, we'll try to keep it 0 if it's corrupted as string
        }
        
        # In a real fix, I would also Re-upload photos if I'm sure of the mapping
        # Let's just fix the TEXT corruption first to make the dashboard usable.
        
        url = f"{BASE_URL}/{record_id}"
        try:
            res = requests.patch(url, headers=HEADERS, json={"fields": fields, "typecast": True})
            if res.status_code == 200:
                print(f"  [OK] Cleaned metadata for {plat_name}")
            else:
                print(f"  [ERROR] {res.status_code}: {res.text}")
        except Exception as e:
            print(f"  [EXCEPTION] {e}")

if __name__ == "__main__":
    clean_data()
