import os
import csv
import sys
import json
import requests
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

# Ajouter le dossier parent au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

class WineImporter:
    def __init__(self):
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.setup_cloudinary()

    def setup_cloudinary(self):
        cloudinary_url = os.getenv("CLOUDINARY_URL", "")
        if cloudinary_url.startswith("cloudinary://"):
            try:
                creds = cloudinary_url.replace("cloudinary://", "")
                key_secret, cloud_name = creds.split("@")
                api_key, api_secret = key_secret.split(":")
                cloudinary.config(cloud_name=cloud_name, api_key=api_key, api_secret=api_secret)
                print("✅ Cloudinary configuré.")
            except Exception as e:
                print(f"⚠️ Erreur config Cloudinary: {e}")

    def upload_image(self, file_path):
        """Upload une image vers Cloudinary si c'est un chemin local."""
        if not file_path or file_path.startswith('http'):
            return file_path
        
        if os.path.exists(file_path):
            try:
                print(f"📤 Uploading {file_path} vers Cloudinary...")
                res = cloudinary.uploader.upload(file_path, folder="restaurant_cherimoya/vins")
                return res.get('secure_url')
            except Exception as e:
                print(f"❌ Erreur upload Cloudinary pour {file_path}: {e}")
                return None
        return None

    def import_csv(self, csv_path):
        if not os.path.exists(csv_path):
            print(f"❌ Fichier non trouvé: {csv_path}")
            return

        print(f"🚀 Début de l'importation depuis {csv_path}...")
        
        with open(csv_path, mode='r', encoding='utf-8') as f:
            # Détection automatique du délimiteur (Excel utilise souvent ; en FR)
            dialect = csv.Sniffer().sniff(f.read(1024))
            f.seek(0)
            reader = csv.DictReader(f, dialect=dialect)
            
            records = []
            for row in reader:
                print(f"🔍 Traitement de: {row.get('Nom')}")
                
                # Gestion de la photo
                photo_url = self.upload_image(row.get('Photo_URL_ou_Chemin', ''))
                
                # Formatage des prix
                def format_price(val):
                    if not val: return ""
                    try:
                        return f"€{float(val.replace(',', '.').strip()):.2f}"
                    except:
                        return val

                fields = {
                    "Nom": row.get('Nom', ''),
                    "Nom_EN": row.get('Nom_EN', ''),
                    "Appellation": row.get('Appellation', ''),
                    "Millesime": str(row.get('Millesime', '')),
                    "Prix_Verre": format_price(row.get('Prix_Verre', '')),
                    "Prix_Bouteille": format_price(row.get('Prix_Bouteille', '')),
                    "Type": row.get('Type', ''),
                    "Description": row.get('Description', ''),
                    "Description_EN": row.get('Description_EN', ''),
                    "Photo": photo_url if photo_url else ""
                }
                
                records.append({"fields": fields})
                
                # Airtable limite à 10 records par requête POST
                if len(records) >= 10:
                    self.push_to_airtable(records)
                    records = []
            
            if records:
                self.push_to_airtable(records)

        print("✨ Importation terminée !")

    def push_to_airtable(self, records):
        url = f"https://api.airtable.com/v0/{self.base_id}/Carte_Vins"
        try:
            response = requests.post(url, headers=self.headers, json={"records": records, "typecast": True})
            if response.status_code == 200:
                print(f"✅ {len(records)} vins ajoutés avec succès.")
            else:
                print(f"❌ Erreur Airtable [{response.status_code}]: {response.text}")
        except Exception as e:
            print(f"❌ Exception lors de l'envoi Airtable: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_vins_excel.py <chemin_vers_csv>")
    else:
        importer = WineImporter()
        importer.import_csv(sys.argv[1])
