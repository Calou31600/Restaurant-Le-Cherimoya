import os
import requests
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

class AssetManager:
    """Gère le transfert et l'optimisation des images vers Cloudinary."""

    def __init__(self):
        # Configuration Cloudinary via l'URL d'environnement
        cloudinary.config(secure=True)
        self.cloud_name = os.getenv('CLOUDINARY_URL').split('@')[-1]

    def upload_from_url(self, image_url, public_id, folder="terroir"):
        """Télécharge une image depuis une URL (ex: Facebook) vers Cloudinary."""
        print(f"Transfert de l'image vers Cloudinary (Dossier: {folder})...")
        try:
            result = cloudinary.uploader.upload(
                image_url,
                public_id=public_id,
                folder=f"restaurant_cherimoya/{folder}",
                overwrite=True,
                resource_type="image"
            )
            print(f"✅ Image transférée avec succès : {result['secure_url']}")
            return result['secure_url']
        except Exception as e:
            print(f"❌ Erreur lors de l'upload: {e}")
            return None

    def get_optimized_url(self, public_id):
        """Génère une URL optimisée avec transformation (auto format, auto quality)."""
        return f"https://res.cloudinary.com/{self.cloud_name}/image/upload/f_auto,q_auto/restaurant_cherimoya/terroir/{public_id}"

if __name__ == "__main__":
    manager = AssetManager()
    # Test avec une image d'exemple (logo Cloudinary)
    sample_url = "https://cloudinary-res.cloudinary.com/image/upload/dpr_2.0,c_scale,w_228/v1/logo_cloudinary_full_composition.png"
    manager.upload_from_url(sample_url, "test_sync_sync")
