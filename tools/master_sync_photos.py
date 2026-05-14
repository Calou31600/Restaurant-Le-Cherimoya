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

BRAIN_DIR = r"C:\Users\pasca\.gemini\antigravity\brain\b916def2-103f-454d-8651-6891a122f715"

# Mapping Global (Photos generees aujourd'hui)
MAPPING = {
    # PLATS & ENTREES
    "brise_asie_soleil_veloute_carotte_premium_1778761164336.png": "Brise d'Asie au soleil",
    "agneau_sublime_pave_selle_premium_1778761183064.png": "Agneau Sublime, Sauce Maison",
    "eclats_poulet_caramel_nouilles_premium_1778761195422.png": "Éclats de Poulet, Saveurs d'Asie",
    "delice_limande_beurre_blanc_premium_1778761214338.png": "Délice de Limande",
    "coleslaw_maison_premium_v2_1778761656145.png": "Coleslaw maison",
    
    # DESSERTS
    "bavarois_individuel_selection_premium_1778761669186.png": "Bavarois Individuel – Sélection",
    
    # BOISSONS
    "7up_glass_bubbles_premium_1778761334542.png": "7up",
    "biere_saigon_bottle_glass_premium_1778761353769.png": "Bière Saigon",
    "biere_pression_pint_premium_1778761376192.png": "Bière pression",
    "jus_ananas_fresh_premium_1778761391908.png": "Jus d'ananas",
    "eau_coco_straw_premium_1778761413109.png": "Eau de coco",
    "infusion_camomille_cup_premium_1778761433491.png": "Infusion camomille",
    "citron_rafraichissant_juice_premium_1778761688237.png": "Citron Rafraîchissant"
}

def master_sync():
    print("--- DEBUT DE LA SYNCHRONISATION MAITRESSE ---")
    
    # 1. Recuperer tous les plats Supabase pour faire un matching intelligent
    res = supabase.table("menu").select("id, plat, photo").execute()
    sb_records = res.data
    
    # 2. Nettoyage des anciennes photos par defaut (Meat/Black Rice)
    # On identifie l'URL de la photo par defaut genante
    DEFAULT_URL_PART = "v1778538688" # C'est le timestamp de la photo de viande
    
    cleaned_count = 0
    for r in sb_records:
        if r.get('photo') and (DEFAULT_URL_PART in r['photo']):
            supabase.table("menu").update({"photo": None}).eq("id", r["id"]).execute()
            cleaned_count += 1
    print(f"[*] {cleaned_count} photos par defaut incoherentes supprimees.")

    # 3. Upload et Matching
    updated_count = 0
    for filename, plat_name in MAPPING.items():
        file_path = os.path.join(BRAIN_DIR, filename)
        if not os.path.exists(file_path):
            print(f"[-] Fichier non trouve : {filename}")
            continue
            
        # Trouver l'ID Supabase correspondant (matching souple sur le nom)
        target_id = None
        target_name_match = None
        for r in sb_records:
            if r['plat'].strip().lower() == plat_name.strip().lower():
                target_id = r['id']
                target_name_match = r['plat']
                break
        
        if not target_id:
            # Essai sans les tirets speciaux ou accents si besoin
            print(f"[!] Impossible de trouver le plat '{plat_name}' dans Supabase.")
            continue
            
        print(f"[>] Uploading {filename} for '{target_name_match}'...")
        try:
            res = cloudinary.uploader.upload(file_path, folder="le_cherimoya_premium_v3")
            photo_url = res.get("secure_url")
            
            supabase.table("menu").update({"photo": photo_url}).eq("id", target_id).execute()
            print(f"[OK] {target_name_match} mis a jour avec succes.")
            updated_count += 1
        except Exception as e:
            print(f"[ERR] {plat_name}: {e}")

    print(f"\n--- SYNCHRONISATION TERMINEE : {updated_count} plats illustres ---")

if __name__ == "__main__":
    master_sync()
