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

# Mapping des boissons générées
BRAIN_DIR = r"C:\Users\pasca\.gemini\antigravity\brain\355ae883-6e3c-4edb-b196-429aaa1b6d2c"

DRINK_UPDATES = {
    "c0cb2021-844a-4133-9a15-9781d6064d56": "biere_saigon_bottle_glass_premium_1778789774418.png",
    "c1ce97f4-3218-422d-acb2-c5365dbc93ce": "biere_pression_pint_premium_1778789789926.png",
    "7f5dea9b-db60-4f08-be87-c85f2be8af93": "citron_rafraichissant_drink_premium_1778789806331.png",
    "cf5be736-074b-4fb7-b2fb-f5e5fdf7a670": "the_noir_cup_premium_bag_1778789817834.png",
    "1cc3d54d-1bd8-4c26-bcc2-8e6384bea020": "jus_ananas_fresh_premium_1778789832627.png",
    "26107a39-db73-4bda-8d17-28da96bb8771": "eau_coco_straw_premium_1778789847797.png",
    "332924f7-2898-4a50-b789-4fa1408538c4": "infusion_camomille_cup_premium_flowers_1778789862812.png"
}

def sync_drinks():
    for item_id, filename in DRINK_UPDATES.items():
        file_path = os.path.join(BRAIN_DIR, filename)
        if not os.path.exists(file_path):
            print(f"[-] Fichier non trouvé : {file_path}")
            continue
            
        print(f"[>] Uploading {filename} for ID {item_id}...")
        try:
            res = cloudinary.uploader.upload(file_path, folder="restaurant_drinks_v2")
            photo_url = res.get("secure_url")
            
            if photo_url:
                supabase.table("menu").update({"photo": photo_url}).eq("id", item_id).execute()
                print(f"[OK] ID {item_id} mis à jour avec {photo_url}")
            else:
                print(f"[ERR] Échec upload Cloudinary pour {filename}")
        except Exception as e:
            print(f"[ERR] Erreur pour {item_id}: {e}")

if __name__ == "__main__":
    sync_drinks()
