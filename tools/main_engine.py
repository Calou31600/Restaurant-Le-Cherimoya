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

if __name__ == "__main__":
    app = MainEngine()
    data = app.build_page_data()
    print(f"--- Données de la Page ---")
    print(f"Ambiance: {data['ui_style']}")
    print(f"NB Plats: {len(data['menu'])}")
    print(f"SEO OK (JSON-LD généré)")
