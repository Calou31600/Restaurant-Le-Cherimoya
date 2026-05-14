import os
import json
import cloudinary
import cloudinary.uploader
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Config Cloudinary
cloudinary_url = os.environ.get("CLOUDINARY_URL", "")
if cloudinary_url.startswith("cloudinary://"):
    creds = cloudinary_url.replace("cloudinary://", "")
    key_secret, cloud_name = creds.split("@")
    api_key, api_secret = key_secret.split(":")
    cloudinary.config(cloud_name=cloud_name, api_key=api_key, api_secret=api_secret)

# Config Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Mapping Fichier -> Nom du Plat
MAPPING = {
    "coleslaw_maison_premium.png": "Coleslaw maison",
    "brise_asie_soleil_premium.png": "Brise d'Asie au soleil",
    "nouilles_poulet_premium.png": "Nouilles sautées au poulet – Style Asiatique",
    "nouilles_boeuf_premium.png": "Nouilles sautées au bœuf – Style Asiatique",
    "bavarois_selection_premium.png": "Bavarois Individuel – Sélection",
    "biere_saigon_premium.png": "Bière Saigon",
    "biere_pression_premium.png": "Bière pression",
    "citron_rafraichissant_premium.png": "Citron Rafraîchissant",
    "the_noir_en_sachet_premium.png": "Thé noir en sachet",
    "jus_ananas_premium.png": "Jus d'ananas",
    "eau_coco_premium.png": "Eau de coco",
    "infusion_camomille_premium.png": "Infusion camomille"
}

def sync_missing_photos():
    img_dir = os.path.join("Photos Menu", "Generated")
    
    print(f"--- Debut de la synchronisation des photos ({len(MAPPING)} cibles) ---")
    
    for filename, plat_name in MAPPING.items():
        file_path = os.path.join(img_dir, filename)
        if not os.path.exists(file_path):
            print(f"[-] Fichier non trouve : {file_path}")
            continue
            
        print(f"[>] Uploading {filename} for '{plat_name}'...")
        try:
            # 1. Upload Cloudinary
            res = cloudinary.uploader.upload(file_path, folder="restaurant_menu")
            photo_url = res.get("secure_url")
            
            # 2. Update Supabase
            supabase.table("menu").update({"photo": photo_url}).eq("plat", plat_name).execute()
            print(f"[OK] {plat_name} mis a jour avec success.")
            
        except Exception as e:
            print(f"[ERR] Erreur pour {plat_name}: {e}")

    print("\nSynchronisation terminee !")

if __name__ == "__main__":
    sync_missing_photos()
