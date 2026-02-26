# SOP : Implémentation Weather-Driven Menu & Header

## Objectif
Modifier dynamiquement l'affichage du site web (Header et Plats Signature mis en avant) en fonction des conditions météorologiques renvoyées par l'API OpenWeather pour Villeneuve-de-Rivière (Latitude : 43.1215, Longitude : 0.6678).

## Inputs (Entrées)
- Payload JSON renvoyé par le script `tools/weather_engine.py` (via API OpenWeather).
- Température mesurée (`temp` en °C).
- Identifiant météo (`weather.id`) pour caractériser Pluie, Neige, Ciel Clair.

## Logique de Décision (Rules)
1.  **Tag = "Froid"** : Si Température < 12.0 °C.
    - *Action UI* : Thème "Chaleureux/Réconfort", mise en avant des plats taggés `Froid` dans Airtable.
2.  **Tag = "Chaud"** : Si Température >= 22.0 °C.
    - *Action UI* : Thème "Frais/Terrasse", mise en avant des plats taggés `Chaud` ou Rafraîchissants dans Airtable.
3.  **Tag = "Pluie"** : Si l'identifiant météo commence par `2`, `3` ou `5` (Orage, Bruine, Pluie).
    - *Action UI* : Message d'accueil insistant sur "l'abri chaleureux".

## Outputs (Sorties)
- Payload JSON généré par `weather_engine.py` et sauvegardé dans `.tmp/current_weather_state.json`.
- Ce fichier est lu par l'injection Frontend pour déterminer le rendu du DOM.

## Edge Cases (Cas aux limites)
- **Time Out API OpenWeather** : Le système applique par défaut l'état "Neutre" (ni chaud ni froid) afin de ne pas bloquer le chargement du site.
- **Cache** : Pour économiser les crédits API, les données météo doivent être mises en cache localement (`.tmp/weather_cache.json`) pendant au minimum 1 heure avant une nouvelle requête.
