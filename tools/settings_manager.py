import os
import requests
from dotenv import load_dotenv

load_dotenv()

class SettingsManager:
    """Gestionnaire des paramètres du restaurant stockés dans Airtable."""

    def __init__(self):
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        self.table_name = "Settings"  # Nom de la table dans Airtable

        # Valeurs par défaut si aucun paramètre n'est configuré
        self.default_settings = {
            "totalSeats": 50,
            "maxReservationsPerDay": 100,
            "lunchStartTime": "12:00",
            "lunchEndTime": "14:00",
            "dinnerStartTime": "19:00",
            "dinnerEndTime": "22:00",
            "closedDays": [],  # Liste vide = ouvert tous les jours
            "minAdvanceBookingHours": 2,
            "maxAdvanceBookingDays": 90
        }

    def get_settings(self):
        """Récupère les paramètres depuis Airtable ou retourne les valeurs par défaut."""
        url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_name}"
        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                records = response.json().get('records', [])
                if records:
                    # Prendre le premier enregistrement (il ne devrait y en avoir qu'un)
                    fields = records[0].get('fields', {})
                    settings = {
                        "totalSeats": fields.get('totalSeats', self.default_settings['totalSeats']),
                        "maxReservationsPerDay": fields.get('maxReservationsPerDay', self.default_settings['maxReservationsPerDay']),
                        "lunchStartTime": fields.get('lunchStartTime', self.default_settings['lunchStartTime']),
                        "lunchEndTime": fields.get('lunchEndTime', self.default_settings['lunchEndTime']),
                        "dinnerStartTime": fields.get('dinnerStartTime', self.default_settings['dinnerStartTime']),
                        "dinnerEndTime": fields.get('dinnerEndTime', self.default_settings['dinnerEndTime']),
                        "closedDays": fields.get('closedDays', self.default_settings['closedDays']),
                        "minAdvanceBookingHours": fields.get('minAdvanceBookingHours', self.default_settings['minAdvanceBookingHours']),
                        "maxAdvanceBookingDays": fields.get('maxAdvanceBookingDays', self.default_settings['maxAdvanceBookingDays'])
                    }
                    settings['record_id'] = records[0]['id']  # Garder l'ID pour les mises à jour
                    return settings
                else:
                    # Aucun enregistrement trouvé, retourner les valeurs par défaut
                    return self.default_settings
            else:
                print(f"Erreur Airtable Settings GET: {response.status_code}")
                return self.default_settings
        except Exception as e:
            print(f"Erreur lors de la récupération des paramètres: {e}")
            return self.default_settings

    def save_settings(self, settings):
        """Sauvegarde les paramètres dans Airtable (création ou mise à jour)."""
        try:
            # D'abord, vérifier si un enregistrement existe déjà
            url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_name}"
            response = requests.get(url, headers=self.headers, timeout=5)

            if response.status_code == 200:
                records = response.json().get('records', [])

                # Préparer les données
                data = {
                    "totalSeats": settings.get('totalSeats'),
                    "maxReservationsPerDay": settings.get('maxReservationsPerDay'),
                    "lunchStartTime": settings.get('lunchStartTime'),
                    "lunchEndTime": settings.get('lunchEndTime'),
                    "dinnerStartTime": settings.get('dinnerStartTime'),
                    "dinnerEndTime": settings.get('dinnerEndTime'),
                    "closedDays": settings.get('closedDays', []),
                    "minAdvanceBookingHours": settings.get('minAdvanceBookingHours'),
                    "maxAdvanceBookingDays": settings.get('maxAdvanceBookingDays')
                }

                if records:
                    # Mise à jour de l'enregistrement existant
                    record_id = records[0]['id']
                    update_url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_name}/{record_id}"
                    payload = {"fields": data}
                    update_response = requests.patch(update_url, json=payload, headers=self.headers, timeout=5)

                    if update_response.status_code == 200:
                        return {"status": "success", "message": "Paramètres mis à jour"}
                    else:
                        print(f"Erreur Airtable Settings PATCH: {update_response.status_code}, {update_response.text}")
                        return {"status": "error", "error": "Erreur lors de la mise à jour"}
                else:
                    # Création d'un nouvel enregistrement
                    payload = {"fields": data}
                    create_response = requests.post(url, json=payload, headers=self.headers, timeout=5)

                    if create_response.status_code == 200:
                        return {"status": "success", "message": "Paramètres créés"}
                    else:
                        print(f"Erreur Airtable Settings POST: {create_response.status_code}, {create_response.text}")
                        return {"status": "error", "error": "Erreur lors de la création"}
            else:
                return {"status": "error", "error": f"Erreur de communication avec Airtable: {response.status_code}"}

        except Exception as e:
            print(f"Erreur lors de la sauvegarde des paramètres: {e}")
            return {"status": "error", "error": str(e)}
