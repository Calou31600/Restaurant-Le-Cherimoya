"""Dump complet de Dynamic_Menu vers .tmp/dishes_backup_<date>.json."""
import os, json, requests
from datetime import date
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ["AIRTABLE_API_KEY"]
BASE_ID = os.environ["AIRTABLE_BASE_ID"]
HEADERS = {"Authorization": f"Bearer {API_KEY}"}
URL = f"https://api.airtable.com/v0/{BASE_ID}/Dynamic_Menu"

records, url = [], URL
while True:
    r = requests.get(url, headers=HEADERS).json()
    records.extend(r.get("records", []))
    if "offset" in r:
        url = f"{URL}?offset={r['offset']}"
    else:
        break

out = os.path.join(os.path.dirname(__file__), "..", ".tmp", f"dishes_backup_{date.today().isoformat()}.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)
print(f"OK  {len(records)} records -> {out}")
