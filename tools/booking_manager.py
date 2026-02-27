import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

class BookingManager:
    """Gère la logique de réservation sécurisée selon la SOP booking_rules.md."""

    def __init__(self):
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def is_service_accessible(self, service_type, target_date_str):
        """
        Vérifie la règle des 2 heures avant le service.
        service_type: 'Midi' ou 'Soir'
        target_date_str: 'YYYY-MM-DD'
        """
        now = datetime.now()
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        
        # Heures de début de service fixes par SOP
        service_times = {
            'Midi': datetime.combine(target_date, datetime.strptime('12:00', '%H:%M').time()),
            'Soir': datetime.combine(target_date, datetime.strptime('19:30', '%H:%M').time())
        }
        
        service_start = service_times.get(service_type)
        if not service_start:
            return False, "Type de service invalide."

        # Règle des 2 heures
        cutoff_time = service_start - timedelta(hours=2)
        
        if now > cutoff_time:
            return False, f"Réservations en ligne clôturées pour ce service. Merci de nous appeler."
        
        return True, "Service accessible."

    def check_inventory(self, service_type, target_date_str):
        """Vérifie la disponibilité dans la table Inventory d'Airtable."""
        url = f"https://api.airtable.com/v0/{self.base_id}/Inventory"
        params = {
            "filterByFormula": f"AND(service='{service_type}', date='{target_date_str}')"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                records = response.json().get('records', [])
                if not records:
                    return True, "Libre" # Pas d'entrée = Pas encore de réservations
                
                record = records[0]['fields']
                total = record.get('capacite_totale', 0)
                occupied = record.get('reservations_confirmées', 0)
                
                if total - occupied <= 0:
                    return False, "Complet"
                return True, f"Disponible ({total - occupied} places)"
            return False, f"Erreur Airtable: {response.status_code}"
        except Exception as e:
            return False, f"Exception: {e}"

if __name__ == "__main__":
    manager = BookingManager()
    # Test simulation
    today = datetime.now().strftime('%Y-%m-%d')
    ok, msg = manager.is_service_accessible('Midi', today)
    print(f"Test Règle 2h (Midi) : {msg}")
    
    ok_inv, msg_inv = manager.check_inventory('Soir', today)
    print(f"Test Inventaire (Soir) : {msg_inv}")
