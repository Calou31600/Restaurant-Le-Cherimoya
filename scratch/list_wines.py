import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def list_wines():
    res = supabase.table("wines").select("id, nom, appellation, millesime, photo").execute()
    for wine in res.data:
        print(f"ID: {wine['id']} | Nom: {wine['nom']} | Appellation: {wine['appellation']} | Millesime: {wine['millesime']} | Photo: {wine['photo']}")

if __name__ == "__main__":
    list_wines()
