import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
HEADERS = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
BASE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Dynamic_Menu"

def find_by_name(name):
    params = {
        "filterByFormula": f"{{Plat}} = '{name}'"
    }
    res = requests.get(BASE_URL, headers=HEADERS, params=params)
    return res.json().get("records", [])

if __name__ == "__main__":
    names = ["Siu Maï Impériaux", "Siu mai vapeur 5pc", "Ha Kao Vapeur", "Ha Kao aux crevettes 5 pc"]
    for n in names:
        recs = find_by_name(n)
        print(f"Recherche '{n}': {len(recs)} records trouvés.")
        for r in recs:
            print(f"  ID: {r['id']} | Plat: {r['fields'].get('Plat')}")
