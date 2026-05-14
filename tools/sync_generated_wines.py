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
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Mapping des vins générés
BRAIN_DIR = r"C:\Users\pasca\AppData\Roaming\Code\User\globalStorage\google.gemini-antigravity\brain\355ae883-6e3c-4edb-b196-429aaa1b6d2c"
# Note: I'll use the relative path to brain dir if possible, or just the filenames if they are in the current CWD
# Actually the tool says they are in C:\Users\pasca\.gemini\antigravity\brain\355ae883-6e3c-4edb-b196-429aaa1b6d2c
BRAIN_DIR = r"C:\Users\pasca\.gemini\antigravity\brain\355ae883-6e3c-4edb-b196-429aaa1b6d2c"

WINE_UPDATES = {
    "fa4c655b-2087-4e7b-8ba9-688dda0b6047": "loulou_charmeuse_bottle_premium_v2_1778789977433.png",
    "1eb2d65d-4ce0-49a4-b381-d14b0ee60dc5": "mas_baux_bottle_premium_v2_1778789990382.png",
    "936ad7fa-3471-4b80-8700-b01c6cf1e507": "chemin_pelerins_bottle_premium_v2_1778790005270.png",
    "c8a9f416-3ce3-44ae-ae59-7ae530964d32": "cirrus_bottle_premium_v2_1778790018756.png"
}

def sync_wines():
    for item_id, filename in WINE_UPDATES.items():
        file_path = os.path.join(BRAIN_DIR, filename)
        if not os.path.exists(file_path):
            print(f"[-] Fichier non trouvé : {file_path}")
            continue
            
        print(f"[>] Uploading {filename} for Wine ID {item_id}...")
        try:
            res = cloudinary.uploader.upload(file_path, folder="restaurant_wines_v2")
            photo_url = res.get("secure_url")
            
            if photo_url:
                supabase.table("wines").update({"photo": photo_url}).eq("id", item_id).execute()
                print(f"[OK] Wine ID {item_id} mis à jour avec {photo_url}")
            else:
                print(f"[ERR] Échec upload Cloudinary pour {filename}")
        except Exception as e:
            print(f"[ERR] Erreur pour {item_id}: {e}")

if __name__ == "__main__":
    sync_wines()
