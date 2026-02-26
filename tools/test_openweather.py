import os
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv(dotenv_path='../.env')

def test_openweather_connection():
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key or api_key == 'votre_cle_api_openweather_ici':
        print("Erreur : Clé API OpenWeather manquante ou non configurée dans .env.")
        return

    # Coordonnées pour Villeneuve-de-Rivière
    lat = "43.1215"
    lon = "0.6678"
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=fr"

    print("Test de connexion à OpenWeather API...")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            temp = data['main']['temp']
            desc = data['weather'][0]['description']
            print(f"✅ Succès ! Température actuelle à Villeneuve-de-Rivière : {temp}°C, {desc}")
        elif response.status_code == 401:
            print("❌ Erreur 401 : Clé API invalide.")
        else:
            print(f"❌ Erreur {response.status_code} : {response.text}")
    except Exception as e:
        print(f"❌ Exception lors de la connexion : {e}")

if __name__ == "__main__":
    test_openweather_connection()
