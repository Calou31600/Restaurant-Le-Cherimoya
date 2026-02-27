import os
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

# Map filenames to Airtable Records
IMAGE_MAP = {
    "salade_poulet.png": "Salade de poulet croustillant",
    "salade_camembert.png": "Salade de camembert rôti",
    "siu_mai.png": "Siu mai vapeur 5pc",
    "salade_nems.png": "Salade de nems",
    "ha_kao.png": "Ha Kao aux crevettes 5pc",
    "aperitif_nems.png": "Assiette d'apéritif - 4 nems",
    "plateau_fromages.png": "Plateau de fromages mixtes",
    "assiette_charcuterie.png": "Assiette de charcuterie et fromages",
    "americano.png": "Américano",
    "pina_colada.png": "Pina colada",
    "sunset_boulevard.png": "Sunset boulevard",
    "mojito.png": "Mojito",
    "paradis_asiatique.png": "Paradis asiatique",
    "nana_fizz.png": "Nana fizz",
    "poire_trompe_loeil.png": "Poire en trompe-l'œil",
    "joue_boeuf.png": "Joue de bœuf confite au four",
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
    menu_dir = "assets/menu"
    airtable_db = get_airtable_records()
    
    for filename, plat_name in IMAGE_MAP.items():
        img_path = os.path.join(menu_dir, filename)
        if not os.path.exists(img_path):
            print(f"Skipping {filename}, file not found.")
            continue
            
        record_id = airtable_db.get(plat_name)
        if not record_id:
            print(f"Record ID not found for plat: {plat_name}")
            continue
            
        print(f"Uploading {filename} to Cloudinary for {plat_name}...")
        try:
            upload_result = cloudinary.uploader.upload(img_path, folder="menu_photos")
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
                    print(f"✅ {plat_name} mis à jour avec succès.")
                else:
                    print(f"❌ Erreur Airtable pour {plat_name}: {res.text}")
        except Exception as e:
            print(f"❌ Erreur lors de l'upload de {filename}: {e}")

if __name__ == "__main__":
    upload_and_update()
    print("Processus d'upload terminé.")
