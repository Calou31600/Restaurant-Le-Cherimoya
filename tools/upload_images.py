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
    "img_salade_poulet": "Salade de poulet croustillant",
    "img_salade_camembert": "Salade de camembert rôti",
    "img_siu_mai": "Siu mai vapeur 5pc",
    "img_salade_nems": "Salade de nems",
    "img_ha_kao": "Ha Kao aux crevettes 5pc",
    "img_aperitif_nems": "Assiette d'apéritif - 4 nems",
    "img_plateau_fromages": "Plateau de fromages mixtes",
    "img_assiette_charcuterie": "Assiette de charcuterie et fromages",
    "img_americano": "Américano",
    "img_pina_colada": "Pina colada",
    "img_sunset_boulevard": "Sunset boulevard",
    "img_mojito": "Mojito",
    "img_paradis_asiatique": "Paradis asiatique",
    "img_nana_fizz": "Nana fizz",
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
    artifact_dir = r"C:\Users\pasca\.gemini\antigravity\brain\c5e7407d-093a-42d5-84d6-80f5d5adeeba"
    images = glob.glob(os.path.join(artifact_dir, "*.png"))
    
    airtable_db = get_airtable_records()
    
    for img_path in images:
        filename = os.path.basename(img_path)
        matched_plat = None
        for key, plat_name in IMAGE_MAP.items():
            if filename.startswith(key):
                matched_plat = plat_name
                break
                
        if not matched_plat:
            continue
            
        record_id = airtable_db.get(matched_plat)
        if not record_id:
            print(f"Record id not found for {matched_plat}")
            continue
            
        print(f"Uploading {filename} to Cloudinary...")
        upload_result = cloudinary.uploader.upload(img_path)
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
