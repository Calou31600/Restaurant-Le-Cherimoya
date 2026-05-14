import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


class BookingManager:
    """Gère la logique de réservation. 100% Supabase, plus aucun fallback Airtable."""

    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
        self.supabase: Client | None = create_client(url, key) if url and key else None
        if not self.supabase:
            print("⚠️ Supabase credentials missing in BookingManager")
        self.base_url = "https://restaurant-le-cherimoya.vercel.app"

    # ─────────────────────────── Reservations ────────────────────────────────

    def _row_to_fields(self, r):
        """Format Supabase → dict {id, fields:{...}} compatible avec dashboard.html."""
        return {
            "id": r["id"],
            "fields": {
                "Nom":       r.get("nom"),
                "Telephone": r.get("telephone"),
                "Email":     r.get("email"),
                "Date":      r.get("date"),
                "Heure":     r.get("heure"),
                "Service":   r.get("service"),
                "Couverts":  r.get("couverts"),
                "Statut":    r.get("statut"),
                "Notes":     r.get("notes"),
            },
        }

    def get_reservations(self):
        """Toutes les réservations, triées par date décroissante."""
        if not self.supabase:
            return []
        try:
            res = self.supabase.table("reservations").select("*").order("date", desc=True).execute()
            return [self._row_to_fields(r) for r in res.data]
        except Exception as e:
            print(f"[Supabase] Erreur get_reservations: {e}")
            return []

    def get_today_stats(self):
        """Stats du jour : couverts confirmés Midi + Soir + listing détaillé."""
        paris_tz = ZoneInfo("Europe/Paris")
        today_str = datetime.now(paris_tz).strftime("%Y-%m-%d")
        stats = {
            "midi": 0, "soir": 0, "date": today_str,
            "reservations_midi": [], "reservations_soir": [],
        }
        if not self.supabase:
            return stats
        try:
            res = (self.supabase.table("reservations")
                   .select("*")
                   .eq("date", today_str)
                   .execute())
            for r in res.data:
                service = r.get("service")
                covers = int(r.get("couverts") or 0)
                statut = (r.get("statut") or "").lower()
                resa_info = {
                    "id":        r.get("id"),
                    "nom":       r.get("nom") or "Inconnu",
                    "couverts":  covers,
                    "heure":     r.get("heure") or "",
                    "telephone": r.get("telephone") or "",
                    "email":     r.get("email") or "",
                    "statut":    r.get("statut") or "À confirmer",
                }
                is_confirmed = statut in ("confirmée", "confirmee")
                if service == "Midi":
                    if is_confirmed: stats["midi"] += covers
                    stats["reservations_midi"].append(resa_info)
                elif service == "Soir":
                    if is_confirmed: stats["soir"] += covers
                    stats["reservations_soir"].append(resa_info)
        except Exception as e:
            print(f"[STATS] Erreur Supabase: {e}")
        return stats

    # ─────────────────────────── Règles métier ───────────────────────────────

    def is_service_accessible(self, service_type, target_date_str):
        """Règle des 2h avant le service + fermeture lundi/mardi."""
        paris_tz = ZoneInfo("Europe/Paris")
        now = datetime.now(paris_tz)
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        today = now.date()

        if target_date.weekday() in [0, 1]:
            return False, "Le restaurant est fermé le lundi et le mardi."

        if target_date > today:
            return True, "Service accessible."
        if target_date < today:
            return False, "Impossible de réserver pour une date passée."

        service_times = {
            "Midi": datetime.combine(target_date, datetime.strptime("12:00", "%H:%M").time()),
            "Soir": datetime.combine(target_date, datetime.strptime("19:30", "%H:%M").time()),
        }
        service_start = service_times.get(service_type)
        if not service_start:
            return False, "Type de service invalide."
        cutoff_time = service_start - timedelta(hours=2)
        if now > cutoff_time:
            return False, "Réservations en ligne clôturées pour ce service aujourd'hui. Merci de nous appeler."
        return True, "Service accessible."

    def check_inventory(self, service_type, target_date_str):
        """Vérifie la disponibilité dans la table `availability`."""
        if not self.supabase:
            return True, "Disponible"
        try:
            res = (self.supabase.table("availability")
                   .select("*")
                   .eq("date", target_date_str)
                   .eq("service", service_type)
                   .execute())
            if not res.data:
                return True, "Disponible (30 places)"
            r = res.data[0]
            total = r.get("capacite_totale", 30)
            occupied = r.get("reservations_confirmees", 0)
            available = total - occupied
            if available <= 0:
                return False, "Complet"
            return True, f"Disponible ({available} places)"
        except Exception as e:
            print(f"[Supabase] Erreur inventory: {e}")
            return True, "Disponible"

    # ─────────────────────────── Mutations résa ──────────────────────────────

    def submit_reservation(self, name, phone, email, date_str, time_str, service, covers):
        """Réservation publique. Soumise à `is_service_accessible` + inventaire."""
        ok_rules, msg_rules = self.is_service_accessible(service, date_str)
        if not ok_rules: return False, msg_rules
        ok_inv, msg_inv = self.check_inventory(service, date_str)
        if not ok_inv: return False, msg_inv

        data = {
            "nom": name, "telephone": phone, "email": email,
            "date": date_str, "heure": time_str, "service": service,
            "couverts": int(covers), "statut": "À confirmer",
        }
        if not self.supabase:
            return False, "Service indisponible."
        try:
            res = self.supabase.table("reservations").insert(data).execute()
            if res.data:
                self.send_email_notification(res.data[0])
                return True, "Votre demande de réservation a bien été envoyée."
            return False, "Réservation non enregistrée."
        except Exception as e:
            print(f"[Supabase] Erreur submit: {e}")
            return False, "Erreur serveur lors de la réservation."

    def create_manual_reservation(self, name, phone, email, date_str, time_str, service, covers):
        """Action Admin : crée une réservation confirmée sans règle de temps."""
        if not self.supabase:
            return False, "Supabase non configuré."
        data = {
            "nom": name, "telephone": phone, "email": email or "",
            "date": date_str, "heure": time_str, "service": service,
            "couverts": int(covers), "statut": "Confirmée",
        }
        try:
            res = self.supabase.table("reservations").insert(data).execute()
            if res.data:
                try: self._update_crm_from_booking(res.data[0])
                except Exception: pass
                return True, "Réservation manuelle créée avec succès."
            return False, "Insertion échouée."
        except Exception as e:
            return False, str(e)

    def update_reservation_status(self, record_id, action):
        """Confirme ou annule une réservation et notifie le client."""
        status_map = {"confirm": "Confirmée", "cancel": "Annulée"}
        status = status_map.get(action)
        if not status: return False, "Action invalide."
        if not self.supabase: return False, "Supabase non configuré."

        try:
            res_get = self.supabase.table("reservations").select("*").eq("id", record_id).execute()
            if not res_get.data:
                return False, "Réservation introuvable."
            booking_data = res_get.data[0]
            self.supabase.table("reservations").update({"statut": status}).eq("id", record_id).execute()
            self.send_client_response(booking_data, status)
            if action == "confirm":
                self._update_crm_from_booking(booking_data)
            return True, f"Réservation {status.lower()} avec succès."
        except Exception as e:
            print(f"[Supabase] Erreur update_status: {e}")
            return False, "Erreur serveur."

    def delete_reservation(self, record_id):
        if not self.supabase: return False, "Supabase non configuré."
        try:
            self.supabase.table("reservations").delete().eq("id", record_id).execute()
            return True, "Réservation supprimée."
        except Exception as e:
            print(f"[Supabase] Erreur delete: {e}")
            return False, "Erreur serveur."

    # ─────────────────────────── CRM ─────────────────────────────────────────

    def _update_crm_from_booking(self, booking_data):
        """Crée/incrémente la fiche client dans `clients`."""
        email = (booking_data.get("email") or "").strip().lower()
        if not email or not self.supabase:
            return
        try:
            res = self.supabase.table("clients").select("*").eq("email", email).execute()
            if res.data:
                row = res.data[0]
                self.supabase.table("clients").update({
                    "nb_reservations": (row.get("nb_reservations") or 0) + 1,
                    "derniere_visite": booking_data.get("date"),
                }).eq("id", row["id"]).execute()
            else:
                self.supabase.table("clients").insert({
                    "nom":             booking_data.get("nom") or "Inconnu",
                    "email":           email,
                    "telephone":       booking_data.get("telephone") or "",
                    "nb_reservations": 1,
                    "derniere_visite": booking_data.get("date"),
                }).execute()
        except Exception as e:
            print(f"[Supabase] Erreur CRM: {e}")

    # ─────────────────────────── Mails ───────────────────────────────────────

    def _smtp(self):
        return os.getenv("SMTP_USER"), os.getenv("SMTP_PASS")

    def send_client_response(self, booking_data, status):
        """Envoie un mail de confirmation ou de refus au client (clés lowercase)."""
        smtp_user, smtp_pass = self._smtp()
        if not smtp_user or not smtp_pass or not booking_data.get("email"):
            return

        nom = booking_data.get("nom", "")
        couverts = booking_data.get("couverts", "")
        date_str = booking_data.get("date", "")
        heure = booking_data.get("heure", "")

        subject = "Votre réservation au Chérimoya"
        signature = ("\n\nCordialement,\nL'équipe du Chérimoya\n"
                     "3 R.D. 817, 31800 Villeneuve-de-Rivière\n07 56 09 47 24")
        if status == "Confirmée":
            body = (f"Bonjour {nom},\n\nNous avons le plaisir de vous confirmer votre "
                    f"réservation pour {couverts} personnes le {date_str} à {heure}.{signature}")
        else:
            body = (f"Bonjour {nom},\n\nNous sommes au regret de ne pas pouvoir honorer "
                    f"votre demande de réservation pour le {date_str} à {heure}. Vous pouvez "
                    f"nous joindre par téléphone pour tout complément d'information.{signature}")
        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = f"Le Chérimoya <{smtp_user}>"
            msg["To"] = booking_data["email"]
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        except Exception as e:
            print(f"Erreur envoi client: {e}")

    def send_email_notification(self, booking_data):
        """Notifie le restaurant d'une nouvelle réservation (clés lowercase)."""
        smtp_user, smtp_pass = self._smtp()
        restaurant_email = "lecherimoyarestaurant@gmail.com"
        if not smtp_user or not smtp_pass:
            print("ERREUR : SMTP_USER ou SMTP_PASS manquant.")
            return

        record_id = booking_data.get("id", "")
        nom       = booking_data.get("nom", "Inconnu")
        couverts  = booking_data.get("couverts", "")
        date_str  = booking_data.get("date", "")
        heure     = booking_data.get("heure", "")
        telephone = booking_data.get("telephone", "N/A")
        email     = booking_data.get("email", "N/A")

        confirm_url = f"{self.base_url}/api/reservations/action/{record_id}/confirm"
        refuse_url  = f"{self.base_url}/api/reservations/action/{record_id}/cancel"
        dashboard_url = f"{self.base_url}/dashboard"

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #cfa86e;">Nouvelle demande de réservation !</h2>
            <p><b>Nom :</b> {nom}</p>
            <p><b>Couverts :</b> {couverts}</p>
            <p><b>Date :</b> {date_str} à {heure}</p>
            <p><b>Contact :</b> {telephone} / {email}</p>
            <hr>
            <div style="margin-top: 20px;">
                <a href="{confirm_url}" style="background-color: #28a745; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; margin-right: 10px;">CONFIRMER</a>
                <a href="{refuse_url}" style="background-color: #dc3545; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">REFUSER</a>
            </div>
            <p style="font-size: 0.8rem; color: #888; margin-top: 30px;">
                Gérer dans le dashboard : <a href="{dashboard_url}">Ouvrir le tableau de bord</a>
            </p>
        </body>
        </html>
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🔔 Nouvelle Réservation - {nom}"
            msg["From"] = smtp_user
            msg["To"] = restaurant_email
            msg.attach(MIMEText(html, "html"))
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
        except Exception as e:
            print(f"ERREUR CRITIQUE SMTP : {e}")

    def send_review_request(self, client_email, client_name):
        """Envoie un mail demandant un avis Google au client."""
        smtp_user, smtp_pass = self._smtp()
        if not smtp_user or not smtp_pass or not client_email:
            return False, "Configuration SMTP manquante."

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
                    Cordialement,<br>L'équipe du Chérimoya<br>
                    3 R.D. 817, 31800 Villeneuve-de-Rivière
                </p>
            </div>
        </body>
        </html>
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"Le Chérimoya <{smtp_user}>"
            msg["To"] = client_email
            msg.attach(MIMEText(html, "html"))
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            return True, "Demande d'avis envoyée avec succès."
        except Exception as e:
            print(f"Erreur envoi demande avis: {e}")
            return False, str(e)


if __name__ == "__main__":
    manager = BookingManager()
    today = datetime.now().strftime("%Y-%m-%d")
    ok, msg = manager.is_service_accessible("Midi", today)
    print(f"Test Règle 2h (Midi) : {msg}")
    ok_inv, msg_inv = manager.check_inventory("Soir", today)
    print(f"Test Inventaire (Soir) : {msg_inv}")
