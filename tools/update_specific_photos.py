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

# Mapping Fichier Local (complet) -> Nom du Plat
MAPPING = {
    "brise_asie_soleil_veloute_carotte_premium_1778761164336.png": "Brise d'Asie au soleil",
    "agneau_sublime_pave_selle_premium_1778761183064.png": "Agneau Sublime, Sauce Maison",
    "eclats_poulet_caramel_nouilles_premium_1778761195422.png": "Éclats de Poulet, Saveurs d'Asie",
    "delice_limande_beurre_blanc_premium_1778761214338.png": "Délice de Limande"
}

def update_photos():
    # Les fichiers generes par l'IA sont dans le dossier de la session (brain)
    # Mais le tool generate_image donne le chemin absolu.
    # Ici on utilise le chemin relatif si possible ou on cherche.
    
    # NOTE: Les fichiers sont dans C:\Users\pasca\.gemini\antigravity\brain\b916def2-103f-454d-8651-6891a122f715\
    base_dir = r"C:\Users\pasca\.gemini\antigravity\brain\b916def2-103f-454d-8651-6891a122f715"
    
    for filename, plat_name in MAPPING.items():
        file_path = os.path.join(base_dir, filename)
        if not os.path.exists(file_path):
            print(f"[-] Fichier non trouve : {file_path}")
            continue
            
        print(f"[>] Uploading {filename} for '{plat_name}'...")
        try:
            res = cloudinary.uploader.upload(file_path, folder="restaurant_menu_v2")
            photo_url = res.get("secure_url")
            
            supabase.table("menu").update({"photo": photo_url}).eq("plat", plat_name).execute()
            print(f"[OK] {plat_name} mis a jour.")
        except Exception as e:
            print(f"[ERR] {plat_name}: {e}")

if __name__ == "__main__":
    update_photos()
