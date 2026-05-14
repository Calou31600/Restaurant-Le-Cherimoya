#!/usr/bin/env python3
"""
Importe les CSV Airtable de `airtable_exports/` vers Supabase.

Usage :
    python tools/import_from_csv.py                # ajoute aux tables existantes
    python tools/import_from_csv.py --clean        # vide chaque table cible avant import
    python tools/import_from_csv.py --only menu,clients

Variables d'env requises : SUPABASE_URL, SUPABASE_KEY (publishable ou service_role).
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

# Console Windows = cp1252 par défaut → force UTF-8 pour les emojis/accents.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPORTS_DIR = REPO_ROOT / "airtable_exports"


class SupabaseREST:
    """Client minimaliste pour PostgREST. Évite la dépendance au SDK supabase-py
    qui plante sur Python 3.14 (pyiceberg) et ne reconnaît pas les clés
    « publishable » modernes."""

    def __init__(self, url: str, key: str):
        self.url = url.rstrip("/")
        self.headers = {
            "apikey":        key,
            "Authorization": f"Bearer {key}",
            "Content-Type":  "application/json",
        }

    def select(self, table: str, params: dict | None = None):
        r = requests.get(f"{self.url}/rest/v1/{table}",
                         headers=self.headers, params=params or {}, timeout=30)
        r.raise_for_status()
        return r.json()

    def insert(self, table: str, rows: list[dict]):
        r = requests.post(f"{self.url}/rest/v1/{table}",
                          headers={**self.headers, "Prefer": "return=representation"},
                          data=json.dumps(rows, ensure_ascii=False).encode("utf-8"),
                          timeout=60)
        if not r.ok:
            raise RuntimeError(f"{r.status_code}: {r.text}")
        return r.json()

    def update(self, table: str, patch: dict, filters: dict):
        r = requests.patch(f"{self.url}/rest/v1/{table}",
                           headers={**self.headers, "Prefer": "return=representation"},
                           params=filters,
                           data=json.dumps(patch, ensure_ascii=False).encode("utf-8"),
                           timeout=60)
        if not r.ok:
            raise RuntimeError(f"{r.status_code}: {r.text}")
        return r.json()

    def delete_all(self, table: str):
        """Supprime toutes les lignes (filtre `id is not null` = match all)."""
        r = requests.delete(f"{self.url}/rest/v1/{table}",
                            headers=self.headers,
                            params={"id": "neq.00000000-0000-0000-0000-000000000000"},
                            timeout=60)
        if not r.ok:
            raise RuntimeError(f"{r.status_code}: {r.text}")


# ─────────────────────────── Helpers de conversion ────────────────────────────

def to_bool(v):
    if v is None:
        return False
    s = str(v).strip().lower()
    return s in {"true", "vrai", "1", "yes", "oui", "checked", "x"}


def to_int(v, default=None):
    if v in (None, ""):
        return default
    try:
        return int(float(str(v).replace(",", ".").strip()))
    except (ValueError, TypeError):
        return default


def to_float(v, default=None):
    if v in (None, ""):
        return default
    s = str(v).replace("€", "").replace(",", ".").strip()
    try:
        return float(s)
    except (ValueError, TypeError):
        return default


def price_str(v):
    """Garde le format texte « €X.XX » utilisé par les colonnes prix_verre/_bouteille/price."""
    if v in (None, ""):
        return None
    s = str(v).strip()
    return s if s.startswith("€") else f"€{to_float(v, 0):.2f}"


def split_csv_list(v):
    """multipleSelects Airtable → list[str]. Airtable exporte en CSV comme « A, B, C »."""
    if not v:
        return []
    return [x.strip() for x in str(v).split(",") if x.strip()]


def split_lines(v):
    """multilineText → list[str], un élément par ligne non vide."""
    if not v:
        return []
    return [line.strip() for line in str(v).splitlines() if line.strip()]


def parse_iso_date(v):
    if not v:
        return None
    s = str(v).strip()
    # Airtable peut exporter "2026-05-14" ou "5/14/2026" selon la locale
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return s  # laisse PostgREST trancher


def parse_iso_datetime(v):
    if not v:
        return None
    s = str(v).strip()
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(s, fmt).isoformat()
        except ValueError:
            continue
    return s


def parse_json_items(v):
    if not v:
        return []
    try:
        return json.loads(v)
    except json.JSONDecodeError:
        return []


# ─────────────────────────── Mappings par table ───────────────────────────────
# Chaque mapper prend une ligne CSV (dict) et renvoie le dict Supabase à insérer.

def map_menu(row):
    return {
        "plat":                row.get("Plat") or None,
        "plat_en":             row.get("Plat_EN") or None,
        "description_geo":     row.get("description_geo") or None,
        "description_geo_en":  row.get("description_geo_EN") or None,
        "prix":                to_float(row.get("prix"), 0),
        "tags_meteo":          split_csv_list(row.get("tags_meteo")),
        "producteur_local":    row.get("producteur_local") or None,
        "is_featured":         to_bool(row.get("is_featured")),
        "photo":               row.get("Photo") or None,
        "menu":                split_csv_list(row.get("Menu")),
        "intolerances":        split_lines(row.get("intolerances")),
    }


def map_wine(row):
    return {
        "nom":             row.get("Nom") or None,
        "nom_en":          row.get("Nom_EN") or None,
        "appellation":     row.get("Appellation") or None,
        "millesime":       str(row.get("Millesime") or "").strip() or None,
        "prix_verre":      price_str(row.get("Prix_Verre")),
        "prix_bouteille":  price_str(row.get("Prix_Bouteille")),
        "type":            row.get("Type") or None,
        "description":     row.get("Description") or None,
        "description_en":  row.get("Description_EN") or None,
        "photo":           row.get("Photo") or None,
    }


def map_special_menu(row):
    return {
        "name":       row.get("Name") or None,
        "theme":      row.get("Theme") or "personnalise",
        "start_date": parse_iso_date(row.get("Start_Date")),
        "end_date":   parse_iso_date(row.get("End_Date")),
        "active":     to_bool(row.get("Active")),
        "price":      row.get("Price") or None,
        "subtitle":   row.get("Subtitle") or None,
        "entrees":    row.get("Entrees") or "",
        "plats":      row.get("Plats") or "",
        "desserts":   row.get("Desserts") or "",
        "photo":      row.get("Photo") or None,
    }


def map_reservation(row):
    return {
        "nom":       row.get("Nom") or None,
        "email":     row.get("Email") or None,
        "telephone": row.get("Telephone") or None,
        "date":      parse_iso_date(row.get("Date")),
        "heure":     row.get("Heure") or None,
        "service":   row.get("Service") or None,
        "couverts":  to_int(row.get("Couverts"), 2),
        "statut":    row.get("Statut") or "À confirmer",
        "notes":     row.get("Notes") or None,
    }


def map_availability(row):
    return {
        "date":                    parse_iso_date(row.get("Date")),
        "service":                 row.get("Service") or None,
        "capacite_totale":         to_int(row.get("Capacite totale"), 30),
        "reservations_confirmees": to_int(row.get("Reservations confirmees"), 0),
        "statut":                  row.get("Statut") or "Ouvert",
    }


def map_client(row):
    return {
        "nom":                  row.get("Nom") or "Inconnu",
        "email":                row.get("Email") or None,
        "telephone":            row.get("Telephone") or None,
        "nb_reservations":      to_int(row.get("Nb_Reservations"), 0),
        "derniere_visite":      parse_iso_date(row.get("Derniere_Visite")),
        "dernier_avis_envoye":  parse_iso_date(row.get("Dernier_Avis_Envoye")),
        "notes":                row.get("Notes") or None,
    }


def map_commande(row):
    return {
        "ref":     row.get("Ref") or None,
        "table_n": to_int(row.get("Table_N"), 0),
        "items":   parse_json_items(row.get("Items")),
        "total":   to_float(row.get("Total"), 0),
        "statut":  row.get("Statut") or "En attente",
        "heure":   parse_iso_datetime(row.get("Heure")),
        "service": row.get("Service") or None,
        "notes":   row.get("Notes") or None,
    }


# settings est un singleton : on UPDATE id=1 plutôt qu'INSERT.
def map_settings(row):
    closed = row.get("closedDays") or ""
    # multipleSelects → ["0","1",...]
    days = [x.strip() for x in closed.split(",") if x.strip()]
    return {
        "total_seats":               to_int(row.get("totalSeats"), 50),
        "max_reservations_per_day":  to_int(row.get("maxReservationsPerDay"), 100),
        "lunch_start_time":          row.get("lunchStartTime") or "12:00",
        "lunch_end_time":            row.get("lunchEndTime") or "14:00",
        "dinner_start_time":         row.get("dinnerStartTime") or "19:00",
        "dinner_end_time":           row.get("dinnerEndTime") or "22:00",
        "closed_days":               days,
        "min_advance_booking_hours": to_int(row.get("minAdvanceBookingHours"), 2),
        "max_advance_booking_days":  to_int(row.get("maxAdvanceBookingDays"), 90),
    }


# ─────────────────────────── Définition des imports ───────────────────────────

IMPORTS = [
    {"name": "menu",          "csv": "Dynamic_Menu.csv",       "mapper": map_menu},
    {"name": "wines",         "csv": "Carte_Vins.csv",         "mapper": map_wine},
    {"name": "special_menus", "csv": "Special_Menus.csv",      "mapper": map_special_menu},
    {"name": "reservations",  "csv": "Reservations.csv",       "mapper": map_reservation},
    {"name": "availability",  "csv": "Disponibilites.csv",     "mapper": map_availability},
    {"name": "clients",       "csv": "Clients.csv",            "mapper": map_client},
    {"name": "commandes",     "csv": "Commandes.csv",          "mapper": map_commande},
    {"name": "settings",      "csv": "Settings_Cherimoya.csv", "mapper": map_settings, "singleton": True},
]


# ─────────────────────────── Boucle principale ────────────────────────────────

def read_csv(path: Path):
    """Lit un CSV Airtable. Airtable peut exporter en UTF-8 ou UTF-8-BOM."""
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def import_table(sb: SupabaseREST, spec: dict, clean: bool):
    csv_path = EXPORTS_DIR / spec["csv"]
    if not csv_path.exists():
        print(f"⏭️  {spec['name']:14s} → {spec['csv']} absent, ignoré")
        return

    rows = read_csv(csv_path)
    print(f"📥 {spec['name']:14s} ← {spec['csv']} ({len(rows)} lignes)")

    if spec.get("singleton"):
        if not rows:
            print("   (CSV vide)")
            return
        payload = spec["mapper"](rows[0])
        sb.update(spec["name"], payload, {"id": "eq.1"})
        print("   ✅ settings mis à jour")
        return

    if clean:
        print(f"   [clean] vide {spec['name']}…", end=" ", flush=True)
        sb.delete_all(spec["name"])
        print("ok")

    payloads = [spec["mapper"](r) for r in rows]
    inserted = 0
    BATCH = 50
    for i in range(0, len(payloads), BATCH):
        chunk = payloads[i:i + BATCH]
        try:
            res = sb.insert(spec["name"], chunk)
            inserted += len(res or chunk)
        except Exception as e:
            print(f"   ❌ batch {i}-{i+len(chunk)} : {e}")
    print(f"   ✅ {inserted}/{len(payloads)} lignes insérées")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true",
                        help="vide chaque table cible avant import")
    parser.add_argument("--only", default="",
                        help="liste de tables à importer, séparées par des virgules")
    args = parser.parse_args()

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("❌ SUPABASE_URL ou SUPABASE_KEY manquant dans .env", file=sys.stderr)
        sys.exit(1)

    sb = SupabaseREST(url, key)
    only = {t.strip() for t in args.only.split(",") if t.strip()}

    for spec in IMPORTS:
        if only and spec["name"] not in only:
            continue
        import_table(sb, spec, args.clean)

    print("\n🎉 Terminé.")


if __name__ == "__main__":
    main()
