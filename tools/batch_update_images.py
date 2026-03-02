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
    "tataki_boeuf": "Tataki de bœuf 250gr",
    "gambas_grillees_3pc": "Grosses gambas grillées 3pc",
    "paradis_asiatique_cocktail": "Paradis asiatique",
    "cotes_agneau_herbes": "Côtes d’agneau grillés aux herbes",
    "tiramisu_cafe_cherimoya": "Tiramisu au café",
    "poire_trompe_oeil_cherimoya": "Poire en trompe-l'œil",
    "gambas_grillees_3pc_v2": "Grosses gambas grillées 3pc",
    "paradis_asiatique_cocktail_v2": "Paradis asiatique",
    "cotes_agneau_herbes_v2": "Côtes d’agneau grillés aux herbes",
    "tiramisu_cafe_v2_cherimoya": "Tiramisu au café",
    "poire_trompe_oeil_v2_cherimoya": "Poire en trompe-l'œil",
    "assiette_charcuterie_fromages_v2": "Assiette de charcuterie et fromages",
    "mojito_cocktail_v2": "Mojito",
    "virgin_colada_cocktail_v2": "Virgin colada",
    "americano_cocktail": "Américano",
    "pates_fruits_de_mer": "Pâtes aux fruits de mer",
    "riz_saute_fruits_de_mer": "Riz sauté aux fruits de mer",
    "pina_colada_cocktail": "Pina colada",
    "nems_poulet_croustillants": "4 nems poulet croustillants",
    "salade_camembert_roti": "Salade de camembert roti",
    "siu_mai_vapeur_5pc_v2_cherimoya_retry": "Siu mai vapeur 5pc",
    "saumon_teriyaki_v2_cherimoya_retry": "Saumon sauce teriyaki",
    "siu_mai_vapeur_cherimoya": "Siu mai vapeur 5pc",
    "filet_bar_beurre_cherimoya": "Filet de bar au beurre",
    "sunset_boulevard_cocktail_cherimoya": "Sunset boulevard",
    "canard_caramel_balsamique_cherimoya": "Filet de canard sauce caramel balsamique",
    "salade_poulet_croustillant_cherimoya_retry": "Salade de poulet croustillant",
    "assiette_fruits_mer_cherimoya_retry": "Assiette de fruits de mer",
    "creme_brulee_cafe_cherimoya_retry": "Crème Brûlée au Café",
    "nana_fizz_cocktail_cherimoya_retry": "Nana fizz",
    "plateau_fromages_mixtes_cherimoya_retry": "Plateau de fromages mixtes",
    "salade_nems_cherimoya_retry": "Salade de nems",
    "joue_boeuf_confite_cherimoya_final": "Joue de bœuf confite au four",
    "faux_filet_boeuf_cherimoya_final": "Faux filet de bœuf 250gr",
    "virgin_mojito_mocktail_cherimoya_final": "Virgin mojito",
    "moules_creme_beurre_cherimoya_final_retry": "Moules à la crème beurre",
    "ha_kao_crevettes_cherimoya_final_retry": "Ha Kao aux crevettes 5 pc",
    "tropezienne_cherimoya_last_chance": "Tropézienne",
    "dome_rubis_cherimoya_last_chance": "Dôme rubis"
}

BRAIN_DIR = r"C:\Users\pasca\.gemini\antigravity\brain\73d8d8ce-532a-4501-afb8-d03e70feb6f3"

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
