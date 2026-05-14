import os
import cloudinary
import cloudinary.uploader
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Config Cloudinary
cloudinary_url = os.environ.get("CLOUDINARY_URL", "")
if cloudinary_url.startswith("cloudinary://"):
    creds = cloudinary_url.replace("cloudinary://", "")
    key_secret, cloud_name = creds.split("@")
    api_key, api_secret = key_secret.split(":")
    cloudinary.config(cloud_name=cloud_name, api_key=api_key, api_secret=api_secret)

# Config Supabase
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

WINE_IMAGES = {
    "3878ec51-9b99-4ea4-9543-8328a7873211": {
        "nom": "Les Déesses Muettes 'EXCEPTION'",
        "url": "https://laboxavin.fr/cdn/shop/files/Sanstitre_800x800px_26_1_0db785d6-bbcc-41ed-bbb1-f570afbf97fa_grande.jpg?v=1749334076"
    },
    "fa4c655b-2087-4e7b-8ba9-688dda0b6047": {
        "nom": "Loulou Charmeuse",
        "url": "https://www.viniou.fr/images/vins/169180_lou-charmeuse-lou.jpg"
    },
    "1eb2d65d-4ce0-49a4-b381-d14b0ee60dc5": {
        "nom": "Mas Baux",
        "url": "https://www.mas-baux.com/wp-content/uploads/2024/02/LOULOU.png"
    },
    "936ad7fa-3471-4b80-8700-b01c6cf1e507": {
        "nom": "Chemin des Pèlerins",
        "url": "https://www.vinogourmets.fr/656-large_default/saint-mont-rouge-2021-chemin-des-pelerins-vigneron-producteurs-plaimont-75cl-.jpg"
    },
    "c8a9f416-3ce3-44ae-ae59-7ae530964d32": {
        "nom": "Cirrus",
        "url": "https://legoutdesvins.fr/wp-content/uploads/2024/02/cirrus-removebg-preview.png"
    },
    "323a99b3-0b68-49e8-9fa0-db3d692cab8a": {
        "nom": "Laffitte Teston",
        "url": "https://vintageselect31.fr/480-large_default/igp-cotes-de-gascogne-cuvee-frangin-frangine-rose-chateau-laffitte-teston.jpg"
    },
    "06a35c6a-af33-472b-809a-06fbcc09f4fa": {
        "nom": "Les Albérières",
        "url": "https://media-viniou.com/wine-info/579788/vin-blanc-sec-albrieres-2024-france-languedoc-et-roussillon-pays-d-oc-igp-1.jpeg"
    }
}

def sync_wines():
    import requests
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    os.makedirs("temp_wine_images", exist_ok=True)
    
    for wine_id, data in WINE_IMAGES.items():
        print(f"[>] Traitement de : {data['nom']} ({wine_id})...")
        try:
            # Download locally first to bypass Cloudinary's direct-from-URL potential 403s
            ext = data['url'].split('?')[0].split('.')[-1]
            if len(ext) > 4: ext = "jpg"
            local_path = os.path.join("temp_wine_images", f"{wine_id}.{ext}")
            
            resp = requests.get(data['url'], headers=headers, timeout=15)
            if resp.status_code == 200:
                with open(local_path, "wb") as f:
                    f.write(resp.content)
                
                # Upload vers Cloudinary
                res = cloudinary.uploader.upload(local_path, folder="restaurant_wines")
                photo_url = res.get("secure_url")
                
                if photo_url:
                    # Update Supabase
                    supabase.table("wines").update({"photo": photo_url}).eq("id", wine_id).execute()
                    print(f"[OK] Mis à jour : {data['nom']} -> {photo_url}")
                else:
                    print(f"[ERR] Échec upload Cloudinary pour {data['nom']}")
            else:
                print(f"[ERR] Échec téléchargement pour {data['nom']} (Status: {resp.status_code})")
                
        except Exception as e:
            print(f"[ERR] Erreur pour {data['nom']}: {e}")

if __name__ == "__main__":
    sync_wines()
