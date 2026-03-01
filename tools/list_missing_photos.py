import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

KEY = os.environ.get("AIRTABLE_API_KEY")
BASE = os.environ.get("AIRTABLE_BASE_ID")
TABLE = "Dynamic_Menu"
url = f"https://api.airtable.com/v0/{BASE}/{TABLE}"
headers = {"Authorization": f"Bearer {KEY}"}

def get_remaining():
    records = []
    params = {}
    while True:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        if "records" not in data:
            print("Error fetching records:", data)
            break
        records.extend(data["records"])
        if "offset" in data:
            params["offset"] = data["offset"]
        else:
            break
    
    remaining = []
    for r in records:
        fields = r.get("fields", {})
        photo = str(fields.get("Photo", ""))
        if "cloudinary.com" not in photo:
            remaining.append({
                "id": r["id"],
                "plat": fields.get("Plat"),
                "desc": fields.get("description_geo", "")
            })
    return remaining

if __name__ == "__main__":
    rem = get_remaining()
    print(json.dumps(rem, indent=2))
