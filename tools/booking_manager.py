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
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        
        # Règle : Fermé le Lundi (0) et le Mardi (1)
        if target_date.weekday() in [0, 1]:
            return False, "Le restaurant est fermé le lundi et le mardi."
        
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
        """Vérifie la disponibilité dans la table Disponibilités d'Airtable."""
        url = f"https://api.airtable.com/v0/{self.base_id}/Disponibilité%s" % "s" # Handling encoding or literal
        # Actually literal 'Disponibilités' is fine if handled correctly
        url = f"https://api.airtable.com/v0/{self.base_id}/Disponibilités"
        params = {
            "filterByFormula": f"AND(Service='{service_type}', Date='{target_date_str}')"
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                records = response.json().get('records', [])
                if not records:
                    return True, f"Disponible (50 places)"
                
                record = records[0]['fields']
                total = record.get('Capacité totale', 50)
                occupied = record.get('Réservations confirmées', 0)
                
                available = total - occupied
                if available <= 0:
                    return False, "Complet"
                return True, f"Disponible ({available} places)"
            return False, f"Erreur Airtable: {response.status_code}"
        except Exception as e:
            return False, f"Exception: {e}"

    def submit_reservation(self, name, phone, email, date_str, time_str, service, covers):
        """Valide et enregistre la réservation dans Airtable."""
        num_covers = int(covers)
        if num_covers > 50:
            return False, "Pour les groupes de plus de 50 personnes, merci de nous contacter directement par téléphone."
            
        ok_rules, msg_rules = self.is_service_accessible(service, date_str)
        if not ok_rules:
            return False, msg_rules
            
        # On vérifie si les places demandées sont disponibles
        ok_inv, msg_inv = self.check_inventory(service, date_str)
        if not ok_inv:
            return False, msg_inv
            
        # Extraction du nombre de places dispo depuis le message (ex: "Disponible (45 places)")
        import re
        try:
            available_match = re.search(r'\((\d+) places\)', msg_inv)
            if available_match:
                available = int(available_match.group(1))
                if num_covers > available:
                    return False, f"Désolé, il ne reste que {available} places disponibles pour ce service."
        except:
            pass
            
        url = f"https://api.airtable.com/v0/{self.base_id}/Reservations"
        fields = {
            "Nom": name,
            "Telephone": phone,
            "Email": email,
            "Date": date_str,
            "Heure": time_str,
            "Service": service,
            "Couverts": int(covers),
            "Statut": "À confirmer"
        }
        try:
            res = requests.post(url, headers=self.headers, json={"records": [{"fields": fields}], "typecast": True})
            if res.status_code == 200:
                self.send_email_notification(fields)
                return True, "Votre demande de réservation a bien été envoyée."
            return False, f"Erreur serveur: {res.text}"
        except Exception as e:
            return False, "Erreur réseau lors de la réservation."

    def send_email_notification(self, booking_data):
        """Envoie une notification par mail au restaurant."""
        # Note : Pour que cela fonctionne sur Vercel, il faut configurer des variables SMTP
        # ou utiliser un service comme SendGrid. Pour l'instant on log l'intention.
        print(f"NOTIFICATION EMAIL: Nouvelle réservation de {booking_data['Nom']} pour {booking_data['Couverts']} personnes le {booking_data['Date']} à {booking_data['Heure']}")
        
        # Exemple d'implémentation SMTP (nécessite SMTP_USER et SMTP_PASS dans .env)
        import smtplib
        from email.mime.text import MIMEText
        
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASS")
        restaurant_email = "lecherimoyarestaurant@gmail.com"

        if smtp_user and smtp_pass:
            try:
                body = f"""
                Nouvelle réservation reçue !
                
                Nom : {booking_data['Nom']}
                Téléphone : {booking_data['Telephone']}
                Email : {booking_data['Email']}
                Date : {booking_data['Date']}
                Heure : {booking_data['Heure']}
                Couverts : {booking_data['Couverts']}
                
                Gérer sur Airtable : https://airtable.com/{self.base_id}
                """
                msg = MIMEText(body)
                msg['Subject'] = f"Nouvelle Réservation - {booking_data['Nom']}"
                msg['From'] = smtp_user
                msg['To'] = restaurant_email

                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
                print("Email de notification envoyé avec succès.")
            except Exception as e:
                print(f"Erreur lors de l'envoi du mail : {e}")

if __name__ == "__main__":
    manager = BookingManager()
    # Test simulation
    today = datetime.now().strftime('%Y-%m-%d')
    ok, msg = manager.is_service_accessible('Midi', today)
    print(f"Test Règle 2h (Midi) : {msg}")
    
    ok_inv, msg_inv = manager.check_inventory('Soir', today)
    print(f"Test Inventaire (Soir) : {msg_inv}")
