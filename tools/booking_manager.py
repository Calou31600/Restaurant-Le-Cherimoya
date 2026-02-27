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
        self.base_url = "https://restaurant-le-cherimoya.vercel.app"

    def is_service_accessible(self, service_type, target_date_str):
        """
        Vérifie la règle des 2 heures avant le service.
        service_type: 'Midi' ou 'Soir'
        target_date_str: 'YYYY-MM-DD'
        """
        now = datetime.now()
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
        url = f"https://api.airtable.com/v0/{self.base_id}/Disponibilites"
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
                total = record.get('Capacite totale', 50)
                occupied = record.get('Reservations confirmees', 0)
                
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
                record_id = res.json()['records'][0]['id']
                self.send_email_notification(fields, record_id)
                return True, "Votre demande de réservation a bien été envoyée."
            return False, f"Erreur serveur: {res.text}"
        except Exception as e:
            return False, "Erreur réseau lors de la réservation."

    def update_reservation_status(self, record_id, action):
        """Met à jour le statut dans Airtable et notifie le client."""
        status_map = {
            "confirm": "Confirmée",
            "cancel": "Annulée"
        }
        status = status_map.get(action)
        if not status:
            return False, "Action invalide."

        url = f"https://api.airtable.com/v0/{self.base_id}/Reservations/{record_id}"
        try:
            # 1. Récupérer les infos de la résa
            res_get = requests.get(url, headers=self.headers)
            if res_get.status_code != 200: 
                return False, f"Réservation introuvable (ID: {record_id})."
            data = res_get.json()['fields']
            
            # 2. Update Airtable
            res_patch = requests.patch(url, headers=self.headers, json={"fields": {"Statut": status}})
            if res_patch.status_code == 200:
                self.send_client_response(data, status)
                return True, f"Réservation {status.lower()} avec succès."
            
            print(f"ERREUR AIRTABLE PATCH: {res_patch.status_code} - {res_patch.text}")
            return False, f"Erreur Airtable ({res_patch.status_code})."
        except Exception as e:
            print(f"EXCEPTION UPDATE STATUS: {e}")
            return False, str(e)

    def send_client_response(self, booking_data, status):
        """Envoie un mail de confirmation ou de refus au client."""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASS")
        if not smtp_user or not smtp_pass or not booking_data.get('Email'): return

        subject = "Votre réservation au Chérimoya"
        signature = "\n\nCordialement,\nL'équipe du Chérimoya\n3 R.D. 817, 31800 Villeneuve-de-Rivière\n07 56 09 47 24"
        
        if status == "Confirmée":
            body = f"Bonjour {booking_data['Nom']},\n\nNous avons le plaisir de vous confirmer votre réservation pour {booking_data['Couverts']} personnes le {booking_data['Date']} à {booking_data['Heure']}.{signature}"
        else:
            body = f"Bonjour {booking_data['Nom']},\n\nNous sommes au regret de ne pas pouvoir honorer votre demande de réservation pour le {booking_data['Date']} à {booking_data['Heure']}. Vous pouvez nous joindre par téléphone pour tout complément d'information.{signature}"

        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = f"Le Chérimoya <{smtp_user}>"
            msg['To'] = booking_data['Email']
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        except Exception as e:
            print(f"Erreur envoi client: {e}")

    def send_email_notification(self, booking_data, record_id):
        """Envoie une notification riche avec boutons au restaurant."""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASS")
        restaurant_email = "lecherimoyarestaurant@gmail.com"

        if smtp_user and smtp_pass:
            try:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = f"🔔 Nouvelle Réservation - {booking_data['Nom']}"
                msg['From'] = smtp_user
                msg['To'] = restaurant_email

                print(f"Tentative d'envoi d'e-mail à {restaurant_email} via {smtp_user}...")

                confirm_url = f"{self.base_url}/api/reservations/action/{record_id}/confirm"
                refuse_url = f"{self.base_url}/api/reservations/action/{record_id}/cancel"

                html = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <h2 style="color: #cfa86e;">Nouvelle demande de réservation !</h2>
                    <p><b>Nom :</b> {booking_data['Nom']}</p>
                    <p><b>Couverts :</b> {booking_data['Couverts']}</p>
                    <p><b>Date :</b> {booking_data['Date']} à {booking_data['Heure']}</p>
                    <p><b>Contact :</b> {booking_data.get('Telephone', 'N/A')} / {booking_data.get('Email', 'N/A')}</p>
                    <hr>
                    <div style="margin-top: 20px;">
                        <a href="{confirm_url}" style="background-color: #28a745; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; margin-right: 10px;">CONFIRMER</a>
                        <a href="{refuse_url}" style="background-color: #dc3545; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">REFUSER</a>
                    </div>
                    <p style="font-size: 0.8rem; color: #888; margin-top: 30px;">
                        Gérer sur Airtable : <a href="https://airtable.com/{self.base_id}">Accéder à la base</a>
                    </p>
                </body>
                </html>
                """
                msg.attach(MIMEText(html, 'html'))

                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                    print("Connexion au serveur SMTP Gmail...")
                    server.login(smtp_user, smtp_pass)
                    print("Authentification réussie.")
                    server.send_message(msg)
                    print("E-mail envoyé avec succès !")
            except Exception as e:
                print(f"ERREUR CRITIQUE SMTP : {e}")
        else:
            print("ERREUR : SMTP_USER ou SMTP_PASS manquant dans les variables d'environnement.")

if __name__ == "__main__":
    manager = BookingManager()
    # Test simulation
    today = datetime.now().strftime('%Y-%m-%d')
    ok, msg = manager.is_service_accessible('Midi', today)
    print(f"Test Règle 2h (Midi) : {msg}")
    
    ok_inv, msg_inv = manager.check_inventory('Soir', today)
    print(f"Test Inventaire (Soir) : {msg_inv}")
