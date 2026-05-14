import os
import json
import cloudinary
import cloudinary.uploader
import unicodedata
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

def normalize(text):
    """Normalise le texte pour faciliter le matching (minuscules, sans accents, sans ponctuation)."""
    if not text: return ""
    text = str(text).lower()
    text = "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    # Remplacer les tirets et ponctuations par des espaces
    for char in "-–—_.,;:()":
        text = text.replace(char, " ")
    return " ".join(text.split())

def force_sync():
    print("--- DEBUT DE LA SYNCHRONISATION FORCEE ---")
    
    # 1. Recuperer tous les plats Supabase
    res = supabase.table("menu").select("id, plat, photo").execute()
    sb_records = res.data
    normalized_sb = {normalize(r['plat']): r for r in sb_records}
    
    # 2. Scanner les dossiers de photos locales
    local_photos = {}
    
    # Dossier Generated
    gen_dir = os.path.join("Photos Menu", "Generated")
    if os.path.exists(gen_dir):
        for f in os.listdir(gen_dir):
            if f.endswith(('.png', '.jpg', '.jpeg')):
                # On essaie d'extraire le nom du plat du nom de fichier
                # Ex: "jus_de_litchi_premium_1778575595950.png" -> "jus de litchi"
                name_part = f.split('_premium')[0].replace('_', ' ')
                local_photos[normalize(name_part)] = os.path.join(gen_dir, f)

    # Dossier de session (pour les toutes dernieres generees)
    brain_dir = r"C:\Users\pasca\.gemini\antigravity\brain\b916def2-103f-454d-8651-6891a122f715"
    if os.path.exists(brain_dir):
        for f in os.listdir(brain_dir):
            if f.endswith('.png') and ('_premium' in f or '_v2' in f):
                name_part = f.split('_premium')[0].split('_v2')[0].replace('_', ' ')
                local_photos[normalize(name_part)] = os.path.join(brain_dir, f)

    # 3. Matching et Upload
    # On a une liste de noms normalises. On va boucler sur les records Supabase.
    updated = 0
    for norm_name, record in normalized_sb.items():
        plat_real_name = record['plat']
        
        # On cherche si on a une photo locale qui "contient" ou "match" ce nom
        found_path = None
        
        # Match direct
        if norm_name in local_photos:
            found_path = local_photos[norm_name]
        else:
            # Match partiel (si le nom du fichier est inclus dans le nom du plat ou vice-versa)
            for local_norm, path in local_photos.items():
                if (local_norm in norm_name) or (norm_name in local_norm):
                    found_path = path
                    break
        
        if found_path:
            print(f"[>] Matching '{plat_real_name}' with {os.path.basename(found_path)}...")
            try:
                res = cloudinary.uploader.upload(found_path, folder="le_cherimoya_final")
                new_url = res.get("secure_url")
                supabase.table("menu").update({"photo": new_url}).eq("id", record["id"]).execute()
                print(f" [OK] Mis a jour.")
                updated += 1
            except Exception as e:
                print(f" [ERR] {plat_real_name}: {e}")

    print(f"\n--- TERMINE : {updated} plats illustres proprement ---")

if __name__ == "__main__":
    force_sync()
