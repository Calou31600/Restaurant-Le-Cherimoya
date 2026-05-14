import os
import requests
import time
import json
from dotenv import load_dotenv
from supabase import create_client, Client
from weather_engine import WeatherEngine
from seo_generator import SEOManager
from booking_manager import BookingManager
from google_business_engine import GoogleBusinessEngine

load_dotenv()

class MainEngine:
    """Chef d'orchestre coordonnant les données Supabase et l'intelligence Météo/SEO avec mise en cache."""

    def __init__(self):
        self.weather = WeatherEngine()
        self.seo = SEOManager()
        self.booking = BookingManager()
        self.business = GoogleBusinessEngine()

        # Supabase
        self.sb_url = os.getenv("SUPABASE_URL")
        self.sb_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
        if self.sb_url and self.sb_key:
            self.supabase: Client = create_client(self.sb_url, self.sb_key)
        else:
            self.supabase = None
            print("⚠️ Supabase credentials missing in .env")

        # Système de Cache
        self._cache = {}
        self.cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.tmp', 'airtable_cache.json')
        self._cache_ttl = {
            "menu": 3600,    # 1 heure (au lieu de 2 min)
            "weather": 600, # 10 minutes
            "reviews": 1800, # 30 minutes
            "wines": 3600    # 1 heure
        }
        self._load_file_cache()

    def _load_file_cache(self):
        """Charge le cache depuis le fichier s'il existe."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
                    print(f"[CACHE] Chargé depuis {self.cache_file}")
            except Exception as e:
                print(f"[CACHE] Erreur chargement fichier: {e}")
                self._cache = {}

    def _save_file_cache(self):
        """Sauvegarde le cache actuel dans le fichier."""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[CACHE] Erreur sauvegarde fichier: {e}")

    def _get_cached(self, key):
        if key in self._cache:
            item = self._cache[key]
            # Support de l'ancien format (liste [data, timestamp]) et du nouveau format JSON (dict)
            if isinstance(item, list) and len(item) == 2:
                data, timestamp = item
            elif isinstance(item, dict) and "data" in item and "timestamp" in item:
                data = item["data"]
                timestamp = item["timestamp"]
            else:
                return None

            if time.time() - timestamp < self._cache_ttl.get(key, 0):
                return data
        return None

    def _set_cache(self, key, data):
        self._cache[key] = {"data": data, "timestamp": time.time()}
        self._save_file_cache()

    def clear_cache(self, key=None):
        """Vide le cache (mémoire et fichier)."""
        if key:
            self._cache.pop(key, None)
        else:
            self._cache = {}
        self._save_file_cache()

    def get_featured_menu(self):
        """Récupère tous les plats depuis Supabase (avec fallback cache disque)."""
        cached_menu = self._get_cached("menu")
        if cached_menu:
            return cached_menu

        if self.supabase:
            try:
                res = self.supabase.table("menu").select("*").order("plat").execute()
                records = [{"id": r["id"], "fields": {
                    "Plat":                r.get("plat"),
                    "Plat_EN":             r.get("plat_en"),
                    "description_geo":     r.get("description_geo") or "",
                    "description_geo_EN":  r.get("description_geo_en") or "",
                    "prix":                f"€{r['prix']:.2f}" if r.get('prix') is not None else "",
                    "tags_meteo":          r.get("tags_meteo") or [],
                    "Menu":                r.get("menu") or [],
                    "intolerances":        r.get("intolerances") or [],
                    "producteur_local":    r.get("producteur_local") or "",
                    "is_featured":         r.get("is_featured") or False,
                    "Photo":               [{"url": r["photo"]}] if r.get("photo") else [],
                }} for r in res.data]
                self._set_cache("menu", records)
                return records
            except Exception as e:
                print(f"[Supabase] Erreur Menu: {e}")

        # Ultime recours : cache disque expiré (si présent)
        return self._cache.get("menu", {}).get("data", [])

    def get_wine_list(self):
        """Récupère tous les vins depuis Supabase."""
        cached = self._get_cached("wines")
        if cached:
            return cached

        if self.supabase:
            try:
                res = self.supabase.table("wines").select("*").order("nom").execute()
                records = [{"id": r["id"], "fields": {
                    "Nom":             r.get("nom"),
                    "Nom_EN":          r.get("nom_en") or r.get("nom"),
                    "Appellation":     r.get("appellation") or "",
                    "Millesime":       r.get("millesime") or "",
                    "Prix_Verre":      r.get("prix_verre"),
                    "Prix_Bouteille": r.get("prix_bouteille"),
                    "Type":            r.get("type") or "Rouge",
                    "Description":     r.get("description") or "",
                    "Description_EN":  r.get("description_en") or "",
                    "Photo":           [{"url": r["photo"]}] if r.get("photo") else [],
                }} for r in res.data]
                self._set_cache("wines", records)
                return records
            except Exception as e:
                print(f"[Supabase] Erreur Vins: {e}")

        return self._cache.get("wines", {}).get("data", [])

    def get_google_reviews(self, lang="fr"):
        """Récupère les avis Google avec cache 30 min.

        Priorité 1 : Google Business Profile API (accès à TOUS les avis,
                     pagination, dates exactes). Nécessite OAuth refresh token.
        Priorité 2 : Places API (New) — fallback limité à 5 avis max,
                     mais traduit automatiquement via languageCode.
        """
        lang = "fr" if lang not in ("fr", "en") else lang
        cache_key = f"reviews:{lang}"
        cached_reviews = self._get_cached(cache_key)
        if cached_reviews:
            return cached_reviews

        # 1. Tentative Business Profile (toutes les reviews)
        if self.business.is_configured():
            try:
                data = self.business.fetch_all_reviews()
                if data and data.get("reviews"):
                    print(f"[Reviews] Business Profile OK — {data['total']} avis, note {data['rating']}, {len(data['reviews'])} avis textuels.")
                    self._set_cache(cache_key, data)
                    return data
                print("[Reviews] Business Profile : aucun avis textuel récupéré, fallback Places API.")
            except Exception as e:
                print(f"[Reviews] Business Profile exception, fallback Places API : {e}")

        # 2. Fallback Places API (New) — 5 avis max, traduits via languageCode
        google_api_key = os.getenv('GOOGLE_API_KEY')
        if not google_api_key:
            print("[Reviews] GOOGLE_API_KEY absente — aucun avis chargé.")
            return None

        place_id = "ChIJw6L9_VP9qBIRmpyHeIKMEXo"
        url = f"https://places.googleapis.com/v1/places/{place_id}"
        headers = {
            "X-Goog-Api-Key": google_api_key,
            "X-Goog-FieldMask": "rating,userRatingCount,reviews",
            "Accept-Language": lang
        }
        params = {"languageCode": lang}
        try:
            response = requests.get(url, headers=headers, params=params, timeout=5)
            if response.status_code != 200:
                print(f"[Reviews] Places API (New) HTTP {response.status_code} : {response.text[:200]}")
                return None

            data = response.json()
            raw_reviews = data.get("reviews", []) or []
            raw_reviews.sort(key=lambda r: r.get("publishTime", ""), reverse=True)

            normalized = []
            for r in raw_reviews:
                text_block = r.get("text") or {}
                text = text_block.get("text") if isinstance(text_block, dict) else None
                if not text:
                    continue
                author = (r.get("authorAttribution") or {}).get("displayName", "Client Google")
                normalized.append({
                    "author_name": author,
                    "rating": r.get("rating"),
                    "text": text,
                    "publishTime": r.get("publishTime", ""),
                    "relative_time": r.get("relativePublishTimeDescription", "")
                })

            reviews_data = {
                "rating": data.get("rating", 4.3),
                "total": data.get("userRatingCount", 66),
                "reviews": normalized
            }
            print(f"[Reviews] Places API fallback ({lang}) — {reviews_data['total']} avis, note {reviews_data['rating']}, {len(normalized)} avis textuels.")
            self._set_cache(cache_key, reviews_data)
            return reviews_data
        except Exception as e:
            print(f"[Reviews] Exception Places API (New) : {e}")
            return None

    def build_page_data(self, lang="fr"):
        """Assemble toutes les données nécessaires pour le frontend avec optimisation des performances."""
        # 1. Obtenir la météo (mise en cache gérée dans weather_engine ou ici)
        # Pour simplifier, on gère le cache météo ici aussi
        cached_weather = self._get_cached("weather")
        if not cached_weather:
            tag, style, msg = self.weather.get_suggested_tag_and_ui()
            cached_weather = (tag, style, msg)
            self._set_cache("weather", cached_weather)
        
        tag, style, msg = cached_weather
        
        # 2. Obtenir le menu (mis en cache)
        raw_menu = self.get_featured_menu()
        menu_items = [r['fields'] for r in raw_menu]

        # 3. Obtenir la carte des vins
        raw_wines = self.get_wine_list()
        wine_items = [r['fields'] for r in raw_wines]

        # 4. Générer le SEO JSON-LD
        json_ld = self.seo.generate_json_ld(menu_items)

        # 5. Avis Google (langue passée par le frontend)
        reviews = self.get_google_reviews(lang=lang)

        return {
            "météo_tag": tag,
            "ui_style": style,
            "welcome_message": msg,
            "menu": menu_items,
            "wines": wine_items,
            "json_ld": json_ld,
            "reviews": reviews
        }

    def get_clients(self):
        """Récupère tous les clients depuis la table Supabase `clients`.

        Format de sortie : liste de `{id, fields}` (clés Airtable-like) pour
        rester compatible avec la fiche admin (dashboard.html `fetchClients`)."""
        if not self.supabase:
            return []
        try:
            res = self.supabase.table("clients").select("*").order("derniere_visite", desc=True).execute()
            return [{
                "id": r["id"],
                "fields": {
                    "Nom":                  r.get("nom"),
                    "Email":                r.get("email"),
                    "Telephone":            r.get("telephone"),
                    "Nb_Reservations":      r.get("nb_reservations") or 0,
                    "Derniere_Visite":      r.get("derniere_visite"),
                    "Dernier_Avis_Envoye":  r.get("dernier_avis_envoye"),
                    "Notes":                r.get("notes"),
                    "Note":                 r.get("note"),
                    "Avis_Recu":            r.get("avis_recu") or False,
                },
            } for r in res.data]
        except Exception as e:
            print(f"Erreur Supabase Clients: {e}")
            return []

    def sync_clients_from_reservations(self):
        """Synchronise la table `clients` depuis les réservations confirmées.

        Dédoublonnage sur l'email. Création ou mise à jour de `derniere_visite`
        et compteur `nb_reservations`."""
        if not self.supabase:
            return False, "Supabase non configuré."
        try:
            # 1. Réservations confirmées
            res = (self.supabase.table("reservations")
                   .select("*")
                   .eq("statut", "Confirmée")
                   .execute())
            reservations = res.data or []

            # 2. Clients existants indexés par email
            cli = self.supabase.table("clients").select("id,email,derniere_visite,nb_reservations,nom,telephone").execute()
            by_email = {c["email"]: c for c in (cli.data or []) if c.get("email")}

            created, updated = 0, 0
            for r in reservations:
                email = (r.get("email") or "").strip().lower()
                if not email:
                    continue
                nom = r.get("nom") or "Inconnu"
                tel = r.get("telephone")
                date_res = r.get("date")

                existing = by_email.get(email)
                if existing:
                    patch = {}
                    if date_res and date_res != existing.get("derniere_visite"):
                        patch["derniere_visite"] = date_res
                        patch["nb_reservations"] = (existing.get("nb_reservations") or 0) + 1
                    if not existing.get("nom") and nom:
                        patch["nom"] = nom
                    if not existing.get("telephone") and tel:
                        patch["telephone"] = tel
                    if patch:
                        self.supabase.table("clients").update(patch).eq("id", existing["id"]).execute()
                        # Refléter en local pour ne pas double-incrémenter sur deux résas du même client
                        existing.update(patch)
                        updated += 1
                else:
                    new_row = {
                        "nom": nom,
                        "email": email,
                        "telephone": tel,
                        "nb_reservations": 1,
                        "derniere_visite": date_res,
                    }
                    ins = self.supabase.table("clients").insert(new_row).execute()
                    by_email[email] = (ins.data or [new_row])[0]
                    created += 1
            return True, f"Synchronisation OK : {created} créé(s), {updated} mis à jour."
        except Exception as e:
            return False, str(e)

if __name__ == "__main__":
    app = MainEngine()
    data = app.build_page_data()
    print(f"--- Données de la Page ---")
    print(f"Ambiance: {data['ui_style']}")
    print(f"NB Plats: {len(data['menu'])}")
    print(f"SEO OK (JSON-LD généré)")
