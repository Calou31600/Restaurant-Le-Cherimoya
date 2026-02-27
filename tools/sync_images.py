
import os
import requests
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

# Config Airtable
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = "Dynamic_Menu"
HEADERS = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

# Config Cloudinary
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL")
if CLOUDINARY_URL:
    # Format: cloudinary://api_key:api_secret@cloud_name
    creds = CLOUDINARY_URL.replace("cloudinary://", "")
    key_secret, cloud_name = creds.split("@")
    api_key, api_secret = key_secret.split(":")
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret
    )

MAPPING = {
    "americano.png": "Américano",
    "aperitif_nems.png": "4 nems poulet croustillants",
    "assiette_charcuterie.png": "Assiette de charcuterie et fromages",
    "ha_kao.png": "Ha Kao aux crevettes 5 pc",
    "mojito.png": "Mojito",
    "nana_fizz.png": "Nana fizz",
    "pina_colada.png": "Pina colada",
    "plateau_fromages.png": "Plateau de fromages mixtes",
    "poire_trompe_loeil.png": "Poire en trompe-l'œil",
    "salade_camembert.png": "Salade de camembert roti",
    "salade_poulet.png": "Salade de poulet croustillant",
    "siu_mai.png": "Siu mai vapeur 5pc",
    "sunset_boulevard.png": "Sunset boulevard",
    "paradis_asiatique.png": "Paradis asiatique",
    "salade_nems.png": "Salade de nems",
    "joue_boeuf.png": "Joue de bœuf confite au four"
}

def get_airtable_records():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME}"
    all_records = []
    offset = None
    while True:
        params = {"offset": offset} if offset else {}
        res = requests.get(url, headers=HEADERS, params=params)
        if res.status_code != 200:
            print(f"Error fetching Airtable: {res.text}")
            break
        data = res.json()
        all_records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    return all_records

def sync():
    print("Fetching Airtable records...")
    records = get_airtable_records()
    if not records:
        print("No records found in Airtable.")
        return

    # Index records by Plat name
    record_map = {r["fields"].get("Plat"): r["id"] for r in records}

    assets_dir = "assets/menu"
    for filename, plat_name in MAPPING.items():
        filepath = os.path.join(assets_dir, filename)
        if not os.path.exists(filepath):
            print(f"Skipping {filename}: file not found.")
            continue
        
        if plat_name not in record_map:
            print(f"Skipping {filename}: Plat '{plat_name}' not found in Airtable.")
            continue

        record_id = record_map[plat_name]
        print(f"Processing '{plat_name}' with {filename}...")

        # Upload to Cloudinary
        try:
            upload_result = cloudinary.uploader.upload(filepath, folder="menu_items")
            img_url = upload_result.get("secure_url")
            print(f"  Uploaded to Cloudinary: {img_url}")

            # Update Airtable
            update_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME}/{record_id}"
            # Airtable Photo field expects an array of objects with 'url'
            payload = {
                "fields": {
                    "Photo": [{"url": img_url}]
                }
            }
            u_res = requests.patch(update_url, headers=HEADERS, json=payload)
            if u_res.status_code == 200:
                print(f"  ✅ Airtable updated for '{plat_name}'")
            else:
                print(f"  ❌ Error updating Airtable for '{plat_name}': {u_res.text}")

        except Exception as e:
            print(f"  ❌ Error processing {filename}: {e}")

if __name__ == "__main__":
    sync()
