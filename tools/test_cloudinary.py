
import os
import cloudinary
import cloudinary.api
from dotenv import load_dotenv

load_dotenv()

cloudinary_url = os.environ.get("CLOUDINARY_URL")

def test_cloudinary():
    print(f"Test de connexion Cloudinary...")
    url = os.environ.get("CLOUDINARY_URL", "")
    if not url:
        print("❌ Erreur : CLOUDINARY_URL non trouvée dans .env")
        return

    try:
        if url.startswith("cloudinary://"):
            creds = url.replace("cloudinary://", "")
            key_secret, cloud_name = creds.split("@")
            api_key, api_secret = key_secret.split(":")
            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret,
                secure=True
            )
        
        # Tentative de récupération des infos du compte
        res = cloudinary.api.usage()
        print("✅ Connexion réussie !")
        print(f"Cloud Name : {cloudinary.config().cloud_name}")
        print(f"Plan : {res.get('plan')}")
    except Exception as e:
        print(f"❌ Erreur Cloudinary : {e}")

if __name__ == "__main__":
    test_cloudinary()
