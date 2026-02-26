import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path='../.env')

def test_airtable_connection():
    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')

    if not api_key or api_key == 'votre_cle_api_airtable_ici' or not base_id or base_id == 'votre_base_id_ici':
        print("Erreur : Airtable API Key ou Base ID manquants ou non configurés dans .env.")
        return

    # Test d'accès à la base (lecture générique ou tentative d'accès)
    url = f"https://api.airtable.com/v0/{base_id}/Dynamic_Menu"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    print("Test de connexion à Airtable API (Table 'Dynamic_Menu')...")
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            records = len(data.get('records', []))
            print(f"✅ Succès ! Connexion établie. {records} enregistrement(s) trouvé(s) sur la première page.")
        elif response.status_code == 401:
            print("❌ Erreur 401 : Token Airtable (API/PAT) invalide ou expiré.")
        elif response.status_code == 404:
            print(f"❌ Erreur 404 : La base {base_id} ou la table 'Dynamic_Menu' n'existe pas.")
        else:
            print(f"❌ Erreur {response.status_code} : {response.text}")
    except Exception as e:
        print(f"❌ Exception lors de la connexion : {e}")

if __name__ == "__main__":
    test_airtable_connection()
