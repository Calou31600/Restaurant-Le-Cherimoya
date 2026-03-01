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
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # URL de base pour les emails et redirections
        self.base_url = "https://restaurant-le-cherimoya.vercel.app"

    def get_reservations(self):
        """Récupère toutes les réservations triées par date décroissante."""
        url = f"https://api.airtable.com/v0/{self.base_id}/Reservations"
        params = {
            "sort[0][field]": "Date",
            "sort[0][direction]": "desc"
        }
        try:
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                return response.json().get('records', [])
            return []
        except Exception as e:
            print(f"Erreur get_reservations: {e}")
            return []

    def get_today_stats(self):
        """Récupère les statistiques de réservation pour aujourd'hui en comptant les couverts confirmés dans la table Reservations."""
        today_str = datetime.now().strftime('%Y-%m-%d')
        stats = {"midi": 0, "soir": 0, "date": today_str}
        
        url = f"https://api.airtable.com/v0/{self.base_id}/Reservations"
        # On ne compte que les réservations CONFIRMÉES pour aujourd'hui
        # On filtre sur les deux orthographes possibles de 'Confirmée'
        formula = f"AND({{Date}}='{today_str}', OR({{Statut}}='Confirm\u00e9e', {{Statut}}='Confirmee'))"
        params = {
            "filterByFormula": formula
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                records = response.json().get('records', [])
                for record in records:
                    fields = record.get('fields', {})
                    service = fields.get('Service')
                    covers = fields.get('Couverts', 0)
                    if service == 'Midi':
                        stats["midi"] += int(covers)
                    elif service == 'Soir':
                        stats["soir"] += int(covers)
            return stats
        except Exception as e:
            print(f"Erreur get_today_stats: {e}")
            return stats

    def is_service_accessible(self, service_type, target_date_str):
        """
        Vérifie la règle des 2 heures avant le service.
        La règle ne s'applique QUE si la date demandée est aujourd'hui.
        Pour toute date future, la réservation est toujours acceptée.
        service_type: 'Midi' ou 'Soir'
        target_date_str: 'YYYY-MM-DD'
        """
        now = datetime.now()
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        today = now.date()

        # Règle : Fermé le Lundi (0) et le Mardi (1)
        if target_date.weekday() in [0, 1]:
            return False, "Le restaurant est fermé le lundi et le mardi."

        # Si la date est dans le futur (pas aujourd'hui), c'est toujours valid
        if target_date > today:
            return True, "Service accessible."

        # Si la date est passée, on refuse
        if target_date < today:
            return False, "Impossible de réserver pour une date passée."

        # Pour AUJOURD'HUI uniquement : appliquer la règle des 2 heures
        service_times = {
            'Midi': datetime.combine(target_date, datetime.strptime('12:00', '%H:%M').time()),
            'Soir': datetime.combine(target_date, datetime.strptime('19:30', '%H:%M').time())
        }

        service_start = service_times.get(service_type)
        if not service_start:
            return False, "Type de service invalide."

        cutoff_time = service_start - timedelta(hours=2)

        if now > cutoff_time:
            return False, f"Réservations en ligne clôturées pour ce service aujourd'hui. Merci de nous appeler."

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
            "Statut": "\u00c0 confirmer"
        }
        try:
            res = requests.post(url, headers=self.headers, json={"records": [{"fields": fields}], "typecast": True})
            if res.status_code == 200:
                record_id = res.json()['records'][0]['id']
                self.send_email_notification(fields, record_id)
                return True, "Votre demande de réservation a bien été envoyée."
            print(f"ERREUR AIRTABLE POST Réservation [{res.status_code}]: {res.text}")
            return False, f"Erreur serveur lors de l'enregistrement. Veuillez réessayer."
        except Exception as e:
            print(f"EXCEPTION submit_reservation: {e}")
            return False, "Erreur réseau lors de la réservation."

    def update_reservation_status(self, record_id, action):
        """Met à jour le statut dans Airtable et notifie le client."""
        status_map = {
            "confirm": "Confirm\u00e9e",
            "cancel": "Annul\u00e9e"
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
                # Si confirmée, on met à jour le CRM automatiquement
                if action == "confirm":
                    self._update_crm_from_booking(data)
                return True, f"Réservation {status.lower()} avec succès."
            
            print(f"ERREUR AIRTABLE PATCH: {res_patch.status_code} - {res_patch.text}")
            return False, f"Erreur Airtable ({res_patch.status_code})."
        except Exception as e:
            print(f"EXCEPTION UPDATE STATUS: {e}")
            return False, str(e)

    def _update_crm_from_booking(self, booking_data):
        """Met à jour ou crée un client dans le CRM à partir d'une réservation confirmée."""
        email = booking_data.get('Email')
        if not email: return
        
        url = f"https://api.airtable.com/v0/{self.base_id}/Clients"
        headers = self.headers
        
        try:
            # 1. Chercher si le client existe déjà (par email)
            search_params = {"filterByFormula": "{Email}='" + email + "'"}
            res = requests.get(url, headers=self.headers, params=search_params)
            if res.status_code == 200:
                records = res.json().get('records', [])
                if records:
                    # Client existant : Mise à jour des infos et date
                    client_id = records[0]['id']
                    existing_fields = records[0]['fields']
                    
                    # On complète les infos manquantes si besoin
                    updated_fields = {
                        "Derniere_Visite": booking_data.get('Date'),
                        "Nom": existing_fields.get('Nom') or booking_data.get('Nom'),
                        "Telephone": existing_fields.get('Telephone') or booking_data.get('Telephone')
                    }
                    
                    # Incrémenter le nombre de réservations si possible via Airtable (ou on le fait nous-mêmes)
                    # Pour faire simple, on récupère le nb actuel et on fait +1
                    old_nb = existing_fields.get('Nb_Reservations', 0)
                    updated_fields["Nb_Reservations"] = old_nb + 1
                    
                    patch_res = requests.patch(f"{url}/{client_id}", headers=self.headers, json={"fields": updated_fields})
                    if patch_res.status_code != 200:
                        print(f"Erreur PATCH CRM: {patch_res.status_code} - {patch_res.text}")
                else:
                    # Nouveau client : Création
                    new_fields = {
                        "Nom": booking_data.get('Nom'),
                        "Email": email,
                        "Telephone": booking_data.get('Telephone'),
                        "Nb_Reservations": 1,
                        "Derniere_Visite": booking_data.get('Date')
                    }
                    post_res = requests.post(url, headers=self.headers, json={"records": [{"fields": new_fields}], "typecast": True})
                    if post_res.status_code != 200:
                        print(f"Erreur POST CRM: {post_res.status_code} - {post_res.text}")
                    else:
                        print(f"✅ Client '{new_fields.get('Nom')}' créé dans le CRM.")
        except Exception as e:
            print(f"Erreur update CRM: {e}")

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

    def send_review_request(self, client_email, client_name):
        """Envoie un mail demandant un avis Google au client."""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASS")
        if not smtp_user or not smtp_pass or not client_email: return False, "Configuration SMTP manquante."

        place_id = "ChIJw6L9_VP9qBIRmpyHeIKMEXo"
        review_url = f"https://search.google.com/local/writereview?placeid={place_id}"

        subject = "Votre avis nous intéresse - Le Chérimoya"
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #1a1a1a; padding: 30px; border-radius: 10px; color: white; text-align: center;">
                <h2 style="color: #cfa86e;">Merci de votre visite au Chérimoya !</h2>
                <p style="font-size: 1.1rem;">Bonjour {client_name},</p>
                <p>Nous espérons que vous avez passé un excellent moment en notre compagnie.</p>
                <p>Votre satisfaction est notre priorité. Pourriez-vous prendre 30 secondes pour nous laisser un avis sur Google ?</p>
                <div style="margin: 30px 0;">
                    <a href="{review_url}" style="background-color: #cfa86e; color: black; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 1.1rem;">LAISSER UN AVIS</a>
                </div>
                <p style="font-size: 0.9rem; color: #888;">Cela nous aide énormément à faire connaître notre cuisine de terroir et de fusion.</p>
                <hr style="border: 0; border-top: 1px solid #333; margin: 20px 0;">
                <p style="font-size: 0.8rem; color: #666;">
                    Cordialement,<br>
                    L'équipe du Chérimoya<br>
                    3 R.D. 817, 31800 Villeneuve-de-Rivière
                </p>
            </div>
        </body>
        </html>
        """

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"Le Chérimoya <{smtp_user}>"
            msg['To'] = client_email
            msg.attach(MIMEText(html, 'html'))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            return True, "Demande d'avis envoyée avec succès."
        except Exception as e:
            print(f"Erreur envoi demande avis: {e}")
            return False, str(e)

if __name__ == "__main__":
    manager = BookingManager()
    # Test simulation
    today = datetime.now().strftime('%Y-%m-%d')
    ok, msg = manager.is_service_accessible('Midi', today)
    print(f"Test Règle 2h (Midi) : {msg}")
    
    ok_inv, msg_inv = manager.check_inventory('Soir', today)
    print(f"Test Inventaire (Soir) : {msg_inv}")
