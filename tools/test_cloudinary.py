import os
import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path='../.env')

def test_cloudinary_connection():
    cloudinary_url = os.getenv('CLOUDINARY_URL')
    if not cloudinary_url or cloudinary_url == 'cloudinary://votre_api_key:votre_api_secret@votre_cloud_name':
        print("Erreur : CLOUDINARY_URL manquant ou non configuré dans .env.")
        return

    # En Python, la validation complète nécessiterait le SDK `cloudinary`
    # Pour un test HTTP simple du CDN sans SDK (juste pour tester le ping si le cloud_name est connu):
    try:
        cloud_name = cloudinary_url.split('@')[-1]
        url = f"https://res.cloudinary.com/{cloud_name}/image/upload/sample.jpg"
        print(f"Test d'accès public à Cloudinary pour le cloud '{cloud_name}'...")
        response = requests.head(url)
        
        # 200 = sample.jpg présent (comportement par défaut)
        # 404 = cloud name valide mais pas d'image sample
        # 400 = invalid cloud name
        if response.status_code in [200, 404]:
            print(f"✅ Cloudinary URL semble joignable.")
        else:
            print(f"⚠️ Réponse cloud inattendue : {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur lors du parsing ou de la requête : {e}")

if __name__ == "__main__":
    test_cloudinary_connection()
