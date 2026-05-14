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

BRAIN_DIR = r"C:\Users\pasca\.gemini\antigravity\brain\b916def2-103f-454d-8651-6891a122f715"
GEN_DIR = os.path.join("Photos Menu", "Generated")

# Mapping Manuel Ultra-Precis pour les derniers recalcitrants
MAPPING = {
    # Jus & Eaux
    "jus_orange_frais_premium_1778763664293.png": "Jus d'orange",
    "jus_ananas_premium.png": "Jus d'ananas",
    "eau_coco_premium.png": "Eau de coco",
    
    # Autres
    "jus_litchi_frais_premium_1778763687303.png": "Jus de litchi",
    "jus_mangue_frais_premium_1778763702976.png": "Jus de mangue",
    "fanta_orange_glass_premium_1778763721853.png": "Fanta",
    "brise_asie_soleil_premium.png": "Brise d'Asie au soleil"
}

def final_polish():
    print("--- DERNIERE TOUCHE DE SYNCHRONISATION ---")
    
    for filename, plat_name in MAPPING.items():
        # Chercher dans BRAIN ou GEN
        file_path = os.path.join(BRAIN_DIR, filename)
        if not os.path.exists(file_path):
            file_path = os.path.join(GEN_DIR, filename)
            
        if not os.path.exists(file_path):
            print(f"[-] Fichier non trouve : {filename}")
            continue
            
        print(f"[>] Uploading {filename} for '{plat_name}'...")
        try:
            res = cloudinary.uploader.upload(file_path, folder="le_cherimoya_perfection")
            photo_url = res.get("secure_url")
            supabase.table("menu").update({"photo": photo_url}).eq("plat", plat_name).execute()
            print(f" [OK] {plat_name} parfait.")
        except Exception as e:
            print(f" [ERR] {plat_name}: {e}")

    print("\n--- TOUT EST TERMINE ! ---")

if __name__ == "__main__":
    final_polish()
