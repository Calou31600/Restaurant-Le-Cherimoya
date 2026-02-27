
import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = "Dynamic_Menu"
HEADERS = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

def check_missing_photos():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME}"
    records = []
    offset = None
    while True:
        params = {"offset": offset} if offset else {}
        res = requests.get(url, headers=HEADERS, params=params)
        data = res.json()
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
            
    print(f"Total records in Airtable: {len(records)}")
    missing_photos = []
    for r in records:
        fields = r.get("fields", {})
        name = fields.get("Plat")
        if not name: continue
        photos = fields.get("Photo", [])
        if not photos:
            missing_photos.append(name)
        elif len(photos) > 0:
            url_img = photos[0].get("url", "")
            if "placeholder" in url_img.lower() or not url_img:
                missing_photos.append(name)
                
    with open("missing_photos.txt", "w", encoding="utf-8") as f:
        if missing_photos:
            f.write(f"Plats sans photo ({len(missing_photos)}):\n")
            for m in missing_photos:
                f.write(f"- {m}\n")
        else:
            f.write("Tous les plats ont une photo !\n")
    
    print("Check complete. Results in missing_photos.txt")

if __name__ == "__main__":
    check_missing_photos()
