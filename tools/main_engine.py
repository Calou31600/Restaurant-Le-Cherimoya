import os
import requests
import time
from dotenv import load_dotenv
from weather_engine import WeatherEngine
from seo_generator import SEOManager
from booking_manager import BookingManager

load_dotenv()

class MainEngine:
    """Chef d'orchestre coordonnant les données Airtable et l'intelligence Météo/SEO avec mise en cache."""

    def __init__(self):
        self.weather = WeatherEngine()
        self.seo = SEOManager()
        self.booking = BookingManager()
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # Système de Cache simple
        self._cache = {}
        self._cache_ttl = {
            "menu": 300,    # 5 minutes
            "weather": 600, # 10 minutes
            "reviews": 3600 # 1 heure
        }

    def _get_cached(self, key):
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._cache_ttl.get(key, 0):
                return data
        return None

    def _set_cache(self, key, data):
        self._cache[key] = (data, time.time())

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
                # Tri alphabétique direct dans le backend (sur le nom du plat en minuscules pour ignorer la casse)
                records.sort(key=lambda x: x.get('fields', {}).get('Plat', '').strip().lower())
                self._set_cache("menu", records)
                return records
            return []
        except Exception as e:
            print(f"Erreur Airtable Menu: {e}")
            return []

    def get_google_reviews(self):
        """Récupère les avis Google My Business avec cache."""
        cached_reviews = self._get_cached("reviews")
        if cached_reviews:
            return cached_reviews
        
        google_api_key = os.getenv('GOOGLE_API_KEY')
        if not google_api_key:
            return None
            
        place_id = "ChIJw6L9_VP9qBIRmpyHeIKMEXo"
        url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=rating,user_ratings_total,reviews&language=fr&key={google_api_key}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json().get('result', {})
                if data:
                    # On garde les infos essentielles
                    reviews_data = {
                        "rating": data.get("rating", 4.5),
                        "total": data.get("user_ratings_total", 0),
                        "reviews": [{"author_name": r.get("author_name"), "rating": r.get("rating"), "text": r.get("text")} for r in data.get("reviews", []) if r.get("text")]
                    }
                    self._set_cache("reviews", reviews_data)
                    return reviews_data
            return None
        except Exception as e:
            print(f"Erreur Google Reviews: {e}")
            return None

    def build_page_data(self):
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
        
        # 4. Avis Google
        reviews = self.get_google_reviews()
        
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
                    # Client existant : Mise à jour de la date de visite
                    client_id = client_emails[email]
                    client_record = next((c for c in current_clients if c['id'] == client_id), None)
                    if client_record:
                        old_date = client_record['fields'].get('Derniere_Visite', '')
                        # On ne met à jour que si la date de résa est plus récente ou différente
                        if date_res != old_date:
                            requests.patch(f"https://api.airtable.com/v0/{self.base_id}/Clients/{client_id}", 
                                           headers=self.headers, 
                                           json={"fields": {"Derniere_Visite": date_res}})
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
