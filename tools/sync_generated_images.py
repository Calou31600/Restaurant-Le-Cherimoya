import os
import requests
import json
import cloudinary
import cloudinary.uploader
import unicodedata
import difflib
from dotenv import load_dotenv

load_dotenv()

# Configuration
AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
CLOUDINARY_URL = os.environ.get("CLOUDINARY_URL")

if CLOUDINARY_URL and CLOUDINARY_URL.startswith("cloudinary://"):
    creds = CLOUDINARY_URL.replace("cloudinary://", "")
    key_secret, cloud_name = creds.split("@")
    api_key, api_secret = key_secret.split(":")
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret
    )

HEADERS = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
BASE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Dynamic_Menu"

# Mapping manuel pour les cas difficiles (noms très différents)
MANUAL_MAPPING = {
    "tartelette_tatin_premium": "Tartelette aux Pommes Caramélisées",
    "fruits_de_mer_premium": "Assiette Marine",
    "canard_caramel_premium": "Tranches de Magret Caramélisé",
    "joue_boeuf_confite_premium": "Joue de Bœuf Confite aux Herbes, Jus Corsé",
    "siu_mai_premium": "Siu Maï Impériaux",
    "ha_kao_premium": "Ha Kao Vapeur",
    "boeuf_saute_asie_premium": "Bœuf Sauté en Dés, Saveurs d'Asie",
    "boeuf_vermicelles_premium": "Bœuf Vermicelles Frais à l'Asiatique"
}

BRAIN_DIR = r"C:\Users\pasca\Downloads\Programme vibe coding\Restaurant Le Cherimoya\Photos Menu\Generated"

def normalize_string(s):
    if not s: return ""
    # Normalize to NFD and remove accents for fuzzy matching
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    # replace œ with oe
    s = s.replace('œ', 'oe')
    return s.strip().lower()

def get_airtable_records():
    url = BASE_URL
    records = []
    offset = None
    while True:
        params = {}
        if offset:
            params['offset'] = offset
        res = requests.get(url, headers=HEADERS, params=params)
        data = res.json()
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    return records

def update_record(record_id, photo_url):
    url = f"{BASE_URL}/{record_id}"
    payload = {
        "fields": {
            "Photo": photo_url
        },
        "typecast": True
    }
    res = requests.patch(url, headers=HEADERS, json=payload)
    return res.status_code == 200

def find_best_match(filename, at_names):
    # Enlever les extensions et les suffixes comme _premium_...
    clean_name = filename.replace(".png", "").replace(".jpg", "")
    if "_premium" in clean_name:
        clean_name = clean_name.split("_premium")[0]
    
    # Remplacer les underscores par des espaces
    clean_name = clean_name.replace("_", " ")
    
    norm_filename = normalize_string(clean_name)
    
    # 1. Check manual mapping first
    for key, val in MANUAL_MAPPING.items():
        if key in filename:
            return val
            
    # 2. Exact match on normalized names
    for name in at_names:
        if norm_filename == normalize_string(name):
            return name
            
    # 3. Fuzzy match
    matches = difflib.get_close_matches(norm_filename, [normalize_string(n) for n in at_names], n=1, cutoff=0.6)
    if matches:
        # Retrouver le nom original
        for name in at_names:
            if normalize_string(name) == matches[0]:
                return name
                
    return None

def main():
    if not os.path.exists(BRAIN_DIR):
        print(f"Dossier {BRAIN_DIR} non trouvé.")
        return

    print("Fetching Airtable records...")
    at_records = get_airtable_records()
    # Utiliser des noms normalisés pour la correspondance
    plat_to_id = {normalize_string(r["fields"].get("Plat")): r["id"] for r in at_records if r["fields"].get("Plat")}
    at_names = [r["fields"].get("Plat") for r in at_records if r["fields"].get("Plat")]
    
    files = [f for f in os.listdir(BRAIN_DIR) if f.endswith(".png") or f.endswith(".jpg")]
    print(f"Trouvé {len(files)} fichiers dans {BRAIN_DIR}.")
    
    for filename in files:
        matched_plat = find_best_match(filename, at_names)
        
        if not matched_plat:
            print(f"?? Aucun match trouvé pour '{filename}'")
            continue
            
        # Chercher l'ID via le nom normalisé
        record_id = plat_to_id.get(normalize_string(matched_plat))
        
        if not record_id:
            print(f"?? Plat '{matched_plat}' trouvé par matching mais ID absent de l'inventaire.")
            continue
        
        # Check if record already has a photo from our v2 folder (to avoid redundant uploads)
        # For now, let's just upload if it's new
        
        filepath = os.path.join(BRAIN_DIR, filename)
        print(f"-> Match: '{filename}' pour '{matched_plat}'")
        print(f"   Upload vers Cloudinary...")
        
        try:
            upload_result = cloudinary.uploader.upload(filepath, folder="restaurant_cherimoya/menu_v2")
            secure_url = upload_result.get("secure_url")
            
            if secure_url:
                if update_record(record_id, secure_url):
                    print(f"   [OK] Airtable mis à jour !")
                else:
                    print(f"   [ERREUR] Échec mise à jour Airtable")
            else:
                print(f"   [ERREUR] Pas de secure_url")
        except Exception as e:
            print(f"   [ERREUR] {e}")

if __name__ == "__main__":
    main()
