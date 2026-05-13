import os
import requests
import json
import cloudinary
import cloudinary.uploader
import unicodedata
import re
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
    cloudinary.config(cloud_name=cloud_name, api_key=api_key, api_secret=api_secret)

HEADERS = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
BASE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Dynamic_Menu"
BRAIN_DIR = r"Photos Menu\Generated"
MISSING_FILE = "current_missing_photos.json"

def normalize_string(s):
    if not s: return ""
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = s.replace('œ', 'oe')
    s = re.sub(r'[^a-zA-Z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip().lower()

def main():
    if not os.path.exists(MISSING_FILE):
        print(f"Fichier {MISSING_FILE} absent.")
        return

    with open(MISSING_FILE, "r", encoding="utf-8") as f:
        missing_plats = json.load(f)

    name_to_plat = {normalize_string(p["plat"]): p for p in missing_plats}
    print(f"Plats attendus ({len(name_to_plat)}): {list(name_to_plat.keys())}")
    
    files = [f for f in os.listdir(BRAIN_DIR) if f.endswith(".png") or f.endswith(".jpg")]
    print(f"Fichiers trouvés ({len(files)}): {files}")

    results = []

    for filename in files:
        # Extraire le nom du plat du nom de fichier
        # On enlève tout ce qui est après le nom de base
        clean_name = re.sub(r'(_premium)?(_\d+)?\.(png|jpg)$', '', filename)
        clean_name = clean_name.replace("_", " ")
        norm_filename = normalize_string(clean_name)
        
        print(f"Analyse '{filename}' -> norm: '{norm_filename}'")
        
        plat_info = None
        for norm_name, info in name_to_plat.items():
            if norm_name == norm_filename or norm_filename in norm_name or norm_name in norm_filename:
                plat_info = info
                print(f"   MATCH trouvé: {info['plat']}")
                break
        
        if not plat_info:
            # Hardcoded fallbacks if needed
            if "bavarois" in norm_filename:
                plat_info = next((v for k,v in name_to_plat.items() if "bavarois" in k), None)
            elif "ananas" in norm_filename:
                plat_info = next((v for k,v in name_to_plat.items() if "ananas" in k), None)
            elif "nouilles" in norm_filename and "poulet" in norm_filename:
                plat_info = next((v for k,v in name_to_plat.items() if "nouilles" in k and "poulet" in k), None)
            elif "nouilles" in norm_filename and "boeuf" in norm_filename:
                plat_info = next((v for k,v in name_to_plat.items() if "nouilles" in k and "boeuf" in k), None)
            elif "brise" in norm_filename and "asie" in norm_filename:
                plat_info = next((v for k,v in name_to_plat.items() if "brise" in k), None)

        if not plat_info:
            print(f"   AUCUN MATCH")
            continue

        filepath = os.path.join(BRAIN_DIR, filename)
        try:
            print(f"   Upload Cloudinary...")
            upload_result = cloudinary.uploader.upload(filepath, folder="restaurant_cherimoya/menu_v2")
            secure_url = upload_result.get("secure_url")
            
            if secure_url:
                results.append({
                    "plat": plat_info['plat'],
                    "id": plat_info['id'],
                    "url": secure_url,
                    "status": "Airtable Pending (Quota)"
                })
                print(f"   [OK] {secure_url}")
        except Exception as e:
            print(f"   [ERREUR] {e}")

    # Sauvegarder
    with open("sync_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Terminé. {len(results)} records dans sync_results.json")

if __name__ == "__main__":
    main()
