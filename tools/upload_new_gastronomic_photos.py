
import os
import glob
import requests
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")

cloudinary_url = os.environ.get("CLOUDINARY_URL", "")
if cloudinary_url.startswith("cloudinary://"):
    creds = cloudinary_url.replace("cloudinary://", "")
    key_secret, cloud_name = creds.split("@")
    api_key, api_secret = key_secret.split(":")
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret
    )
else:
    cloudinary.config()

TABLE_NAME = "Dynamic_Menu"
BASE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME}"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

IMAGE_MAP = {
    "faux_filet_boeuf": "Faux filet de bœuf 250gr",
    "canard_caramel_balsamique": "Filet de canard sauce caramel balsamique",
    "agneau_herbes": "Côtes d’agneau grillés aux herbes",
    "saumon_teriyaki": "Saumon sauce teriyaki",
    "bar_au_beurre": "Filet de bar au beurre",
    "assiette_fruits_de_mer": "Assiette de fruits de mer",
    "gambas_grillees": "Grosses gambas grillées 3pc",
    "moules_creme_beurre": "Moules à la crème beurre",
    "riz_saute_fruits_mer": "Riz sauté aux fruits de mer",
    "pates_fruits_de_mer": "Pâtes aux fruits de mer",
    "creme_brulee_cafe": "Crème Brûlée au Café",
    "dome_rubis": "Dôme rubis",
    "tartelette_tatin": "Tartelette tatin",
    "tropezienne": "Tropézienne",
    "tiramisu_cafe": "Tiramisu au café",
    "virgin_mojito": "Virgin mojito",
    "virgin_colada": "Virgin colada",
}

def get_airtable_records():
    records = {}
    url = BASE_URL
    while True:
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        if "records" in data:
            for r in data["records"]:
                plat_name = r["fields"].get("Plat")
                if plat_name:
                    records[plat_name] = r["id"]
        if "offset" in data:
            url = f"{BASE_URL}?offset={data['offset']}"
        else:
            break
    return records

def upload_and_update():
    # Use the current artifact directory for this task
    artifact_dir = r"C:\Users\pasca\.gemini\antigravity\brain\49b9e2eb-da5c-4f87-aa44-91c9e4d4e01e"
    images = glob.glob(os.path.join(artifact_dir, "*.png"))
    
    airtable_db = get_airtable_records()
    
    for img_path in images:
        filename = os.path.basename(img_path)
        matched_plat = None
        for key, plat_name in IMAGE_MAP.items():
            if key in filename:
                matched_plat = plat_name
                break
                
        if not matched_plat:
            print(f"No mapping found for {filename}")
            continue
            
        record_id = airtable_db.get(matched_plat)
        if not record_id:
            print(f"Record id not found for {matched_plat}")
            continue
            
        print(f"Uploading {filename} for '{matched_plat}' to Cloudinary...")
        upload_result = cloudinary.uploader.upload(img_path, folder="restaurant_cherimoya/menu")
        img_url = upload_result.get("secure_url")
        
        if img_url:
            patch_url = f"{BASE_URL}/{record_id}"
            payload = {
                "fields": {
                    "Photo": [{"url": img_url}]
                }
            }
            res = requests.patch(patch_url, headers=HEADERS, json=payload)
            if res.status_code == 200:
                print(f"✅ {matched_plat} mis à jour dans Airtable.")
            else:
                print(f"❌ Erreur Airtable: {res.text}")

if __name__ == "__main__":
    upload_and_update()
    print("Processus terminé.")
