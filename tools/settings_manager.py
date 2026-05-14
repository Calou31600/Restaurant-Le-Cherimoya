import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


class SettingsManager:
    """Gestionnaire des paramètres du restaurant stockés dans Supabase.

    La table `settings` est un singleton (PK fixe à 1, contrainte CHECK).
    La ligne est créée par la migration 004 ; ce gestionnaire ne fait que
    SELECT/UPDATE sur id=1.
    """

    # Mapping camelCase (côté UI / fiche admin) ↔ snake_case (colonnes Supabase)
    _UI_TO_DB = {
        "totalSeats":              "total_seats",
        "maxReservationsPerDay":   "max_reservations_per_day",
        "lunchStartTime":          "lunch_start_time",
        "lunchEndTime":            "lunch_end_time",
        "dinnerStartTime":         "dinner_start_time",
        "dinnerEndTime":           "dinner_end_time",
        "closedDays":              "closed_days",
        "minAdvanceBookingHours":  "min_advance_booking_hours",
        "maxAdvanceBookingDays":   "max_advance_booking_days",
    }
    _DB_TO_UI = {v: k for k, v in _UI_TO_DB.items()}

    DEFAULT_SETTINGS = {
        "totalSeats": 50,
        "maxReservationsPerDay": 100,
        "lunchStartTime": "12:00",
        "lunchEndTime": "14:00",
        "dinnerStartTime": "19:00",
        "dinnerEndTime": "22:00",
        "closedDays": [],
        "minAdvanceBookingHours": 2,
        "maxAdvanceBookingDays": 90,
    }

    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
        self.supabase: Client | None = create_client(url, key) if url and key else None
        if not self.supabase:
            print("⚠️ SettingsManager : SUPABASE_URL/SUPABASE_KEY manquant — fallback aux valeurs par défaut")

    def get_settings(self):
        """Lit la ligne unique `settings` (id=1) et la mappe en camelCase pour l'UI."""
        if not self.supabase:
            return dict(self.DEFAULT_SETTINGS)
        try:
            res = self.supabase.table("settings").select("*").eq("id", 1).execute()
            if not res.data:
                # La ligne devrait toujours exister (seedée par 004) ; sinon défauts.
                return dict(self.DEFAULT_SETTINGS)
            row = res.data[0]
            out = {ui_key: row.get(db_col) for db_col, ui_key in self._DB_TO_UI.items()}
            # Garantit que closedDays est une liste (peut être None si DB cassée)
            if out.get("closedDays") is None:
                out["closedDays"] = []
            return out
        except Exception as e:
            print(f"[Settings] Erreur GET Supabase: {e} — utilisation des défauts")
            return dict(self.DEFAULT_SETTINGS)

    def save_settings(self, settings):
        """UPDATE de la ligne id=1. Renvoie {status, message|error}."""
        if not self.supabase:
            return {"status": "error", "error": "Supabase non configuré"}
        try:
            payload = {}
            for ui_key, db_col in self._UI_TO_DB.items():
                if ui_key in settings:
                    payload[db_col] = settings[ui_key]
            # closed_days doit être list[str]
            if "closed_days" in payload:
                payload["closed_days"] = [str(d) for d in (payload["closed_days"] or [])]
            self.supabase.table("settings").update(payload).eq("id", 1).execute()
            return {"status": "success", "message": "Paramètres mis à jour avec succès"}
        except Exception as e:
            print(f"[Settings] Erreur UPDATE Supabase: {e}")
            return {"status": "error", "error": f"Erreur technique: {e}"}
