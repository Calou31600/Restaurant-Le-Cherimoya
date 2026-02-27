
import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

def test_read_dispo():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Disponibilités"
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    print(f"Test de lecture de 'Disponibilités'...")
    res = requests.get(url, headers=headers)
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text}")

if __name__ == "__main__":
    test_read_dispo()
