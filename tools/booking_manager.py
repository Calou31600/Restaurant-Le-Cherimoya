import os
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

class BookingManager:
    """Gère la logique de réservation sécurisée selon la SOP booking_rules.md."""

    def __init__(self):
        # Supabase
        self.sb_url = os.getenv("SUPABASE_URL")
        self.sb_key = os.getenv("SUPABASE_KEY")
        if self.sb_url and self.sb_key:
            self.supabase: Client = create_client(self.sb_url, self.sb_key)
        else:
            self.supabase = None
            print("⚠️ Supabase credentials missing in BookingManager")

        # Airtable (Backup/Legacy)
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://restaurant-le-cherimoya.vercel.app"

    def get_reservations(self):
        """Récupère toutes les réservations triées par date décroissante via Supabase."""
        if self.supabase:
            try:
                res = self.supabase.table("reservations").select("*").order("date", desc=True).execute()
                return [{"id": r["id"], "fields": {
                    "Nom": r["nom"],
                    "Telephone": r["telephone"],
                    "Email": r["email"],
                    "Date": r["date"],
                    "Heure": r["heure"],
                    "Service": r["service"],
                    "Couverts": r["couverts"],
                    "Statut": r["statut"],
                    "Notes": r["notes"]
                }} for r in res.data]
            except Exception as e:
                print(f"[Supabase] Erreur get_reservations: {e}")

        # Fallback Airtable
        url = f"https://api.airtable.com/v0/{self.base_id}/Reservations"
        try:
            response = requests.get(url, headers=self.headers, params={"sort[0][field]": "Date", "sort[0][direction]": "desc"})
            return response.json().get('records', []) if response.status_code == 200 else []
        except: return []

    def get_today_stats(self):
        """Récupère les statistiques de réservation pour aujourd'hui en comptant les couverts confirmés dans la table Reservations."""
        paris_tz = ZoneInfo("Europe/Paris")
        today_str = datetime.now(paris_tz).strftime('%Y-%m-%d')
        stats = {
            "midi": 0, "soir": 0, "date": today_str,
            "reservations_midi": [], "reservations_soir": []
        }

        url = f"https://api.airtable.com/v0/{self.base_id}/Reservations"
        # On récupère TOUTES les réservations du jour (confirmées et à confirmer)
        formula = f"DATESTR({{Date}})='{today_str}'"
        params = {
            "filterByFormula": formula
        }
        
        try:
            print(f"[STATS] Requête stats du jour: date={today_str}, formula={formula}")
            response = requests.get(url, headers=self.headers, params=params)
            print(f"[STATS] Réponse Airtable: HTTP {response.status_code}")
            if response.status_code == 200:
                records = response.json().get('records', [])
                print(f"[STATS] {len(records)} réservation(s) confirmée(s) trouvée(s) pour {today_str}")
                for record in records:
                    fields = record.get('fields', {})
                    service = fields.get('Service')
                    covers = fields.get('Couverts', 0)
                    
                    resa_info = {
                        "id": record.get('id'),
                        "nom": fields.get('Nom', 'Inconnu'),
                        "couverts": covers,
                        "heure": fields.get('Heure', ''),
                        "telephone": fields.get('Telephone', ''),
                        "email": fields.get('Email', ''),
                        "statut": fields.get('Statut', 'À confirmer')
                    }
                    
                    # On ne compte dans le total que les confirmées
                    is_confirmed = resa_info['statut'].lower() in ['confirmée', 'confirmee']
                    
                    if service == 'Midi':
                        if is_confirmed: stats["midi"] += int(covers)
                        stats["reservations_midi"].append(resa_info)
                    elif service == 'Soir':
                        if is_confirmed: stats["soir"] += int(covers)
                        stats["reservations_soir"].append(resa_info)
            else:
                print(f"[STATS] ERREUR Airtable {response.status_code}: {response.text[:500]}")
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
        paris_tz = ZoneInfo("Europe/Paris")
        now = datetime.now(paris_tz)
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
        """Vérifie la disponibilité dans Supabase (table availability)."""
        if self.supabase:
            try:
                res = self.supabase.table("availability").select("*").eq("date", target_date_str).eq("service", service_type).execute()
                if not res.data:
                    return True, "Disponible (30 places)"
                
                record = res.data[0]
                total = record.get('capacite_totale', 30)
                occupied = record.get('reservations_confirmees', 0)
                available = total - occupied
                if available <= 0: return False, "Complet"
                return True, f"Disponible ({available} places)"
            except Exception as e:
                print(f"[Supabase] Erreur inventory: {e}")

        # Fallback Airtable
        url = f"https://api.airtable.com/v0/{self.base_id}/Disponibilites"
        try:
            response = requests.get(url, headers=self.headers, params={"filterByFormula": f"AND(Service='{service_type}', Date='{target_date_str}')"})
            if response.status_code == 200:
                records = response.json().get('records', [])
                if not records: return True, "Disponible (30 places)"
                r = records[0]['fields']
                available = r.get('Capacite totale', 30) - r.get('Reservations confirmees', 0)
                return (True, f"Disponible ({available} places)") if available > 0 else (False, "Complet")
        except: pass
        return True, "Disponible"

    def submit_reservation(self, name, phone, email, date_str, time_str, service, covers):
        """Enregistre la réservation dans Supabase."""
        num_covers = int(covers)
        ok_rules, msg_rules = self.is_service_accessible(service, date_str)
        if not ok_rules: return False, msg_rules
        
        ok_inv, msg_inv = self.check_inventory(service, date_str)
        if not ok_inv: return False, msg_inv
            
        data = {
            "nom": name,
            "telephone": phone,
            "email": email,
            "date": date_str,
            "heure": time_str,
            "service": service,
            "couverts": num_covers,
            "statut": "À confirmer"
        }

        if self.supabase:
            try:
                res = self.supabase.table("reservations").insert(data).execute()
                if res.data:
                    self.send_email_notification(data, res.data[0]['id'])
                    return True, "Votre demande de réservation a bien été envoyée."
            except Exception as e:
                print(f"[Supabase] Erreur submit: {e}")

        # Fallback Airtable
        try:
            res = requests.post(f"https://api.airtable.com/v0/{self.base_id}/Reservations", headers=self.headers, json={"records": [{"fields": data}], "typecast": True})
            if res.status_code == 200:
                self.send_email_notification(data, res.json()['records'][0]['id'])
                return True, "Votre demande de réservation a été envoyée (via Airtable)."
        except: pass
        return False, "Erreur serveur lors de la réservation."

    def create_manual_reservation(self, name, phone, email, date_str, time_str, service, covers):
        """Action Admin : Crée une réservation confirmée immédiatement, sans règle de temps."""
        url = f"https://api.airtable.com/v0/{self.base_id}/Reservations"
        fields = {
            "Nom": name,
            "Telephone": phone,
            "Email": email if email else "",
            "Date": date_str,
            "Heure": time_str,
            "Service": service,
            "Couverts": int(covers),
            "Statut": "Confirm\u00e9e"
        }
        try:
            res = requests.post(url, headers=self.headers, json={"records": [{"fields": fields}], "typecast": True})
            if res.status_code == 200:
                booking_data = res.json()['records'][0]['fields']
                # On met aussi à jour le CRM
                try:
                    self._update_crm_from_booking(booking_data)
                except:
                    pass
                return True, "Réservation manuelle créée avec succès."
            return False, f"Erreur Airtable: {res.text}"
        except Exception as e:
            return False, str(e)

    def update_reservation_status(self, record_id, action):
        """Met à jour le statut dans Supabase et notifie le client."""
        status_map = {"confirm": "Confirmée", "cancel": "Annulée"}
        status = status_map.get(action)
        if not status: return False, "Action invalide."

        if self.supabase:
            try:
                # 1. Obtenir les infos actuelles
                res_get = self.supabase.table("reservations").select("*").eq("id", record_id).execute()
                if not res_get.data: return False, "Réservation introuvable."
                booking_data = res_get.data[0]
                
                # 2. Update
                self.supabase.table("reservations").update({"statut": status}).eq("id", record_id).execute()
                
                # 3. Notification
                self.send_client_response(booking_data, status)
                if action == "confirm": self._update_crm_from_booking(booking_data)
                return True, f"Réservation {status.lower()} avec succès."
            except Exception as e:
                print(f"[Supabase] Erreur update_status: {e}")

        # Fallback Airtable
        try:
            res = requests.patch(f"https://api.airtable.com/v0/{self.base_id}/Reservations/{record_id}", headers=self.headers, json={"fields": {"Statut": status}})
            return (True, f"Réservation {status.lower()} (Airtable)") if res.status_code == 200 else (False, "Erreur Airtable")
        except: return False, "Erreur réseau"

    def delete_reservation(self, record_id):
        """Supprime une réservation."""
        if self.supabase:
            try:
                self.supabase.table("reservations").delete().eq("id", record_id).execute()
                return True, "Réservation supprimée."
            except Exception as e: print(f"[Supabase] Erreur delete: {e}")

        try:
            res = requests.delete(f"https://api.airtable.com/v0/{self.base_id}/Reservations/{record_id}", headers=self.headers)
            return (True, "Supprimé (Airtable)") if res.status_code == 200 else (False, "Erreur Airtable")
        except: return False, "Erreur réseau"

    def _update_crm_from_booking(self, booking_data):
        """Met à jour le CRM dans Supabase."""
        email = (booking_data.get('email') or booking_data.get('Email', '')).strip()
        if not email: return

        if self.supabase:
            try:
                # 1. Chercher le client
                res = self.supabase.table("clients").select("*").eq("email", email).execute()
                if res.data:
                    cid = res.data[0]['id']
                    nb = res.data[0].get('nb_reservations', 0) + 1
                    self.supabase.table("clients").update({"nb_reservations": nb, "derniere_visite": booking_data.get('date')}).eq("id", cid).execute()
                else:
                    self.supabase.table("clients").insert({
                        "nom": booking_data.get('nom', 'Inconnu'),
                        "email": email,
                        "telephone": booking_data.get('telephone', ''),
                        "nb_reservations": 1,
                        "derniere_visite": booking_data.get('date')
                    }).execute()
            except Exception as e:
                print(f"[Supabase] Erreur CRM: {e}")

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
