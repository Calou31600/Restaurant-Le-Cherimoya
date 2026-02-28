import os
import requests
import json
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

# Configuration
AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
CLOUDINARY_URL = os.environ.get("CLOUDINARY_URL")

if CLOUDINARY_URL.startswith("cloudinary://"):
    creds = CLOUDINARY_URL.replace("cloudinary://", "")
    key_secret, cloud_name = creds.split("@")
    api_key, api_secret = key_secret.split(":")
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret
    )

HEADERS = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
BASE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Dynamic_Menu"

# Mapping - Key is a substring of the filename, Value is the Plat name in Airtable
MAPPING = {
    "canard_sauce_maison": "Filet de canard sauce fait maison",
    "cote_boeuf": "Côte de bœuf 400g",
    "crevettes_ail_beurre": "Crevettes sautées beurre ail",
    "formule_vietnamienne": "Formule Vietnamienne",
    "glaces_chantilly": "Glaces (2 boules au choix)",
    "le_delice_cocktail": "Le délice",
    "lexotique_cocktail": "L'exotique",
    "menu_enfant_cherimoya": "Menu Enfant",
    "poulet_cheddar": "Filet de poulet au cheddar",
    "poulet_teriyaki": "Poulet sauce teriyaki",
    "prohibition_mocktail": "Prohibition",
    "tataki_boeuf": "Tataki de bœuf 250gr"
}

BRAIN_DIR = r"C:\Users\pasca\.gemini\antigravity\brain\2fce4afb-db18-4eaf-b1ff-d10a48040969"

def get_airtable_records():
    url = BASE_URL
    records = []
    while True:
        res = requests.get(url, headers=HEADERS)
        data = res.json()
        records.extend(data.get("records", []))
        if "offset" in data:
            url = f"{BASE_URL}?offset={data['offset']}"
        else:
            break
    return records

def update_record(record_id, photo_url):
    url = f"{BASE_URL}/{record_id}"
    payload = {
        "fields": {
            "Photo": photo_url
        },
        "typecast": True
    }
    res = requests.patch(url, headers=HEADERS, json=payload)
    if res.status_code != 200:
        print(f"Error updating record {record_id}: {res.status_code} - {res.text}")
    return res.status_code == 200

def main():
    print("Fetching Airtable records...")
    at_records = get_airtable_records()
    plat_to_id = {r["fields"].get("Plat"): r["id"] for r in at_records}
    
    files = [f for f in os.listdir(BRAIN_DIR) if f.endswith(".png")]
    
    for filename in files:
        matched_plat = None
        for key, plat_name in MAPPING.items():
            if key in filename:
                matched_plat = plat_name
                break
        
        if not matched_plat:
            print(f"No mapping found for {filename}")
            continue
            
        record_id = plat_to_id.get(matched_plat)
        if not record_id:
            print(f"Record NOT found in Airtable for Plat: {matched_plat}")
            continue
            
        filepath = os.path.join(BRAIN_DIR, filename)
        print(f"Uploading {filename} for {matched_plat}...")
        
        try:
            upload_result = cloudinary.uploader.upload(filepath, folder="restaurant_cherimoya/menu")
            secure_url = upload_result.get("secure_url")
            
            if secure_url:
                print(f"Success. Updating Airtable record {record_id}...")
                if update_record(record_id, secure_url):
                    print(f"Airtable updated for {matched_plat}!")
                else:
                    print(f"FAILED to update Airtable for {matched_plat}")
            else:
                print(f"FAILED to get secure_url for {filename}")
        except Exception as e:
            print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    main()
