# SOP: Weather-Driven Menu Logic (`sop_weather_logic.md`)

## Objectif
Adapter dynamiquement le menu du restaurant et l'affichage du site web en fonction des conditions météorologiques réelles de Villeneuve-de-Rivière via l'API OpenWeather.

## Algorithme de Décision

### 1. Détection des Conditions
Le système interroge OpenWeather API toutes les heures.
- **Température (T)** : Mesurée en Celsius.
- **Condition (C)** : Etat du ciel (Pluie, Soleil, Nuages).

### 2. Règles d'Adaptation
A. **Scénario FROID (T < 12°C)** :
   - Mise en avant des "Plats signatures réconfortants".
   - Modification du Header : Tons chauds, ambiance cocooning.
   - Tag Airtable cible : `Froid`.

B. **Scénario CHAUD (T > 25°C)** :
   - Mise en avant des plats frais, terrasses et cocktails.
   - Tag Airtable cible : `Chaud`.

C. **Scénario PLUIE (Conditions = Rain/Drizzle)** :
   - Message d'accueil : "Venez vous mettre à l'abri au coin du feu".
   - Tag Airtable cible : `Pluie`.

## Intégration Airtable
- Le script `weather_engine.py` filtrera la table `Dynamic_Menu` pour extraire les records ayant le tag correspondant à la météo actuelle.
- Si aucun plat n'a le tag spécifique, le menu par défaut (`is_featured = True`) est affiché.

## Variables de Contrôle
- `THRESHOLD_COLD`: 12
- `THRESHOLD_HOT`: 25
