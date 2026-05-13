import os
import cloudinary
import cloudinary.uploader
import json
from dotenv import load_dotenv

load_dotenv()

# Configuration Cloudinary
CLOUDINARY_URL = os.environ.get("CLOUDINARY_URL")
if CLOUDINARY_URL and CLOUDINARY_URL.startswith("cloudinary://"):
    creds = CLOUDINARY_URL.replace("cloudinary://", "")
    key_secret, cloud_name = creds.split("@")
    api_key, api_secret = key_secret.split(":")
    cloudinary.config(cloud_name=cloud_name, api_key=api_key, api_secret=api_secret)

filepath = r"Photos Menu\Generated\eau_coco_premium.png"
plat_id = "rectUYXudqhxrSZ0s"
plat_name = "Eau de coco"

try:
    print(f"Uploading {plat_name}...")
    upload_result = cloudinary.uploader.upload(filepath, folder="restaurant_cherimoya/menu_v2")
    secure_url = upload_result.get("secure_url")
    
    if secure_url:
        print(f"Success: {secure_url}")
        # Mettre à jour sync_results.json
        with open("sync_results.json", "r", encoding="utf-8") as f:
            results = json.load(f)
        
        results.append({
            "plat": plat_name,
            "id": plat_id,
            "url": secure_url,
            "status": "Airtable Pending (Quota)"
        })
        
        with open("sync_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
except Exception as e:
    print(f"Error: {e}")
