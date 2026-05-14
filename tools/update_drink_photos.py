import os
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

# Mapping Boissons
MAPPING = {
    "7up_glass_bubbles_premium_1778761334542.png": "7up",
    "biere_saigon_bottle_glass_premium_1778761353769.png": "Bière Saigon",
    "biere_pression_pint_premium_1778761376192.png": "Bière pression",
    "jus_ananas_fresh_premium_1778761391908.png": "Jus d'ananas",
    "eau_coco_straw_premium_1778761413109.png": "Eau de coco",
    "infusion_camomille_cup_premium_1778761433491.png": "Infusion camomille"
}

def update_photos():
    base_dir = r"C:\Users\pasca\Downloads\Programme vibe coding\Restaurant Le Cherimoya\tools"
    # Note: Les fichiers sont dans le dossier brain de la session
    brain_dir = r"C:\Users\pasca\.gemini\antigravity\brain\b916def2-103f-454d-8651-6891a122f715"
    
    for filename, plat_name in MAPPING.items():
        file_path = os.path.join(brain_dir, filename)
        if not os.path.exists(file_path):
            print(f"[-] Fichier non trouve : {file_path}")
            continue
            
        print(f"[>] Uploading {filename} for '{plat_name}'...")
        try:
            res = cloudinary.uploader.upload(file_path, folder="restaurant_drinks")
            photo_url = res.get("secure_url")
            
            supabase.table("menu").update({"photo": photo_url}).eq("plat", plat_name).execute()
            print(f"[OK] {plat_name} mis a jour.")
        except Exception as e:
            print(f"[ERR] {plat_name}: {e}")

if __name__ == "__main__":
    update_photos()
