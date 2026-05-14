import os
import requests
from dotenv import load_dotenv

WINE_IMAGES = {
    "3878ec51-9b99-4ea4-9543-8328a7873211": {
        "nom": "Les Déesses Muettes 'EXCEPTION'",
        "url": "https://laboxavin.fr/cdn/shop/files/Sanstitre_800x800px_26_1_0db785d6-bbcc-41ed-bbb1-f570afbf97fa_grande.jpg?v=1749334076"
    },
    "fa4c655b-2087-4e7b-8ba9-688dda0b6047": {
        "nom": "Loulou Charmeuse",
        "url": "https://images.vivino.com/thumbs/GvC_6E_vSceR_C0_W0_pb_600x600.jpg"
    },
    "1eb2d65d-4ce0-49a4-b381-d14b0ee60dc5": {
        "nom": "Mas Baux",
        "url": "https://www.masbaux.com/wp-content/uploads/2021/03/SERIE-B-ROUGE-768x1152.jpg"
    },
    "936ad7fa-3471-4b80-8700-b01c6cf1e507": {
        "nom": "Chemin des Pèlerins",
        "url": "https://www.cavernedelours.com/94-large_default/chemin-des-pelerins-saint-mont-.jpg"
    },
    "c8a9f416-3ce3-44ae-ae59-7ae530964d32": {
        "nom": "Cirrus",
        "url": "https://legoutdesvins.fr/wp-content/uploads/2021/04/Corbieres-Domaine-Cirrus-Exception-scaled.jpg"
    },
    "323a99b3-0b68-49e8-9fa0-db3d692cab8a": {
        "nom": "Laffitte Teston",
        "url": "https://binendswine.com/cdn/shop/products/LaffitteTestonCotesdeGascogneBlancSec.jpg?v=1614714652"
    },
    "06a35c6a-af33-472b-809a-06fbcc09f4fa": {
        "nom": "Les Albérières",
        "url": "https://media-viniou.com/wine-info/579788/vin-blanc-sec-albrieres-2024-france-languedoc-et-roussillon-pays-d-oc-igp-1.jpeg"
    }
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def download_images():
    os.makedirs("temp_wine_images", exist_ok=True)
    for wine_id, data in WINE_IMAGES.items():
        ext = data['url'].split('?')[0].split('.')[-1]
        if len(ext) > 4: ext = "jpg"
        filename = f"{wine_id}.{ext}"
        filepath = os.path.join("temp_wine_images", filename)
        
        print(f"[>] Downloading {data['nom']}...")
        try:
            response = requests.get(data['url'], headers=headers, timeout=15)
            if response.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(response.content)
                print(f"[OK] Saved to {filepath}")
            else:
                print(f"[ERR] Status code {response.status_code} for {data['nom']}")
        except Exception as e:
            print(f"[ERR] Error downloading {data['nom']}: {e}")

if __name__ == "__main__":
    download_images()
