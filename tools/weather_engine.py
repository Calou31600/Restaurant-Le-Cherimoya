import os
import requests
from dotenv import load_dotenv

load_dotenv()

class WeatherEngine:
    """Moteur logique pour adapter le restaurant à la météo de Villeneuve-de-Rivière."""
    
    LAT = "43.1215"
    LON = "0.6678"
    THRESHOLD_COLD = 12
    THRESHOLD_HOT = 25

    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY')

    def get_current_weather(self):
        """Récupère les données météo en temps réel."""
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={self.LAT}&lon={self.LON}&appid={self.api_key}&units=metric&lang=fr"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Erreur Weather API: {e}")
            return None

    def get_suggested_tag_and_ui(self):
        """Détermine le tag Airtable et les recommandations UI basés sur la SOP."""
        data = self.get_current_weather()
        if not data:
            return "Default", "Ambiance Gastronomique", "Découvrez notre carte de saison"

        temp = data['main']['temp']
        conditions = data['weather'][0]['main'].lower()
        
        # Logique basée sur la SOP weather_logic.md
        if "rain" in conditions or "drizzle" in conditions:
            return "Pluie", "Ambiance Cocooning", "Venez vous mettre à l'abri au coin du feu"
        
        if temp < self.THRESHOLD_COLD:
            return "Froid", "Tons Chauds", "Plats signatures réconfortants pour réchauffer les cœurs"
        
        if temp > self.THRESHOLD_HOT:
            return "Chaud", "Ambiance Terrasse", "Fraîcheur et produits de saison en terrasse"
            
        return "Normal", "Standard Premium", "L'excellence du terroir Commingeois"

if __name__ == "__main__":
    engine = WeatherEngine()
    tag, style, msg = engine.get_suggested_tag_and_ui()
    print(f"Météo actuelle -> Tag Airtable: {tag} | Style UI: {style} | Message: {msg}")
