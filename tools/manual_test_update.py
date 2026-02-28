import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
HEADERS = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

def test_update():
    # L'exotique
    record_id = "recA8pJ1frWeSNvt6"
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Dynamic_Menu/{record_id}"
    payload = {
        "fields": {
            "Photo": [{"url": "https://res.cloudinary.com/dytpnnyi0/image/upload/v1772275255/restaurant_cherimoya/menu/lexotique_cocktail.png"}]
        },
        "typecast": True
    }
    res = requests.patch(url, headers=HEADERS, json=payload)
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text}")

if __name__ == "__main__":
    test_update()
