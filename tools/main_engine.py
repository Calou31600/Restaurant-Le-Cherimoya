import os
import requests
import time
import json
from dotenv import load_dotenv
from weather_engine import WeatherEngine
from seo_generator import SEOManager
from booking_manager import BookingManager
from google_business_engine import GoogleBusinessEngine

load_dotenv()

class MainEngine:
    """Chef d'orchestre coordonnant les données Airtable et l'intelligence Météo/SEO avec mise en cache."""

    def __init__(self):
        self.weather = WeatherEngine()
        self.seo = SEOManager()
        self.booking = BookingManager()
        self.business = GoogleBusinessEngine()
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

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
        """Récupère tous les plats depuis Airtable avec mise en cache et tri alphabétique."""
        cached_menu = self._get_cached("menu")
        if cached_menu:
            return cached_menu

        url = f"https://api.airtable.com/v0/{self.base_id}/Dynamic_Menu"
        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                records = response.json().get('records', [])
                records.sort(key=lambda x: x.get('fields', {}).get('Plat', '').strip().lower())
                self._set_cache("menu", records)
                return records
            
            # MODE RÉSILIENT : Si quota dépassé ou erreur, on utilise le cache même s'il est expiré
            print(f"[AIRTABLE] Erreur {response.status_code} sur Menu. Utilisation du fallback cache.")
            if "menu" in self._cache:
                return self._cache["menu"].get("data", [])
            return []
        except Exception as e:
            print(f"Erreur Airtable Menu: {e}")
            if "menu" in self._cache:
                return self._cache["menu"].get("data", [])
            return []

    def get_wine_list(self):
        """Récupère tous les vins depuis Airtable avec mise en cache et tri alphabétique."""
        cached = self._get_cached("wines")
        if cached:
            return cached
        url = f"https://api.airtable.com/v0/{self.base_id}/Carte_Vins"
        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                records = response.json().get('records', [])
                records.sort(key=lambda x: x.get('fields', {}).get('Nom', '').strip().lower())
                self._set_cache("wines", records)
                return records
            
            # FALLBACK
            print(f"[AIRTABLE] Erreur {response.status_code} sur Vins. Utilisation du fallback cache.")
            if "wines" in self._cache:
                return self._cache["wines"].get("data", [])
            return []
        except Exception as e:
            print(f"Erreur Airtable Vins: {e}")
            if "wines" in self._cache:
                return self._cache["wines"].get("data", [])
            return []

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
        
        # 3. Générer le SEO JSON-LD
        json_ld = self.seo.generate_json_ld(menu_items)
        
        # 4. Avis Google (langue passée par le frontend)
        reviews = self.get_google_reviews(lang=lang)
        
        return {
            "météo_tag": tag,
            "ui_style": style,
            "welcome_message": msg,
            "menu": menu_items,
            "json_ld": json_ld,
            "reviews": reviews
        }

    def get_clients(self):
        """Récupère tous les clients depuis la table Clients."""
        url = f"https://api.airtable.com/v0/{self.base_id}/Clients"
        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            if response.status_code == 200:
                return response.json().get('records', [])
            return []
        except Exception as e:
            print(f"Erreur Airtable Clients: {e}")
            return []

    def sync_clients_from_reservations(self):
        """
        Synchronise les clients à partir de la table Reservations.
        Dédoublonnage basé sur l'email.
        """
        # 1. Récupérer toutes les réservations confirmées
        res_url = f"https://api.airtable.com/v0/{self.base_id}/Reservations"
        params = {"filterByFormula": "{Statut}='Confirmée'"}
        try:
            res_response = requests.get(res_url, headers=self.headers, params=params)
            reservations = res_response.json().get('records', [])
            
            # 2. Récupérer les clients actuels pour dédoublonnage
            current_clients = self.get_clients()
            client_emails = {c['fields'].get('Email'): c['id'] for c in current_clients if c['fields'].get('Email')}
            
            # 3. Traiter les réservations
            for res_record in reservations:
                fields = res_record['fields']
                email = fields.get('Email')
                if not email: continue
                
                nom = fields.get('Nom')
                tel = fields.get('Telephone')
                date_res = fields.get('Date')
                
                if email in client_emails:
                    client_id = client_emails[email]
                    client_record = next((c for c in current_clients if c['id'] == client_id), None)
                    if client_record:
                        existing_fields = client_record.get('fields', {})
                        
                        # On met à jour si la date est différente ou si des infos manquent
                        update_needed = False
                        new_fields = {}
                        
                        if date_res != existing_fields.get('Derniere_Visite'):
                            new_fields["Derniere_Visite"] = date_res
                            update_needed = True
                            
                        if not existing_fields.get('Nom') and nom:
                            new_fields["Nom"] = nom
                            update_needed = True
                            
                        if not existing_fields.get('Telephone') and tel:
                            new_fields["Telephone"] = tel
                            update_needed = True

                        if update_needed:
                            requests.patch(f"https://api.airtable.com/v0/{self.base_id}/Clients/{client_id}", 
                                           headers=self.headers, 
                                           json={"fields": new_fields})
                else:
                    # Nouveau client : Création
                    new_client_fields = {
                        "Nom": nom,
                        "Email": email,
                        "Telephone": tel,
                        "Nb_Reservations": 1,
                        "Derniere_Visite": date_res
                    }
                    requests.post(f"https://api.airtable.com/v0/{self.base_id}/Clients", 
                                  headers=self.headers, 
                                  json={"records": [{"fields": new_client_fields}], "typecast": True})
                    # On l'ajoute au cache local pour éviter les doublons dans la même boucle
                    client_emails[email] = "new"
            return True, "Synchronisation terminée."
        except Exception as e:
            return False, str(e)

if __name__ == "__main__":
    app = MainEngine()
    data = app.build_page_data()
    print(f"--- Données de la Page ---")
    print(f"Ambiance: {data['ui_style']}")
    print(f"NB Plats: {len(data['menu'])}")
    print(f"SEO OK (JSON-LD généré)")
