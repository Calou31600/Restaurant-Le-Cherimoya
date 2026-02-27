# Gemini - Project Constitution (Restaurant Le Cherimoya)

## Data Schemas (JSON)

### 1. Dynamic_Menu (Airtable)
```json
{
  "id": "string (Airtable ID)",
  "plat": "string",
  "description_geo": "string (Optimisé pour IA/Moteurs)",
  "tags_meteo": ["Froid", "Chaud", "Pluie"],
  "prix": "number",
  "producteur_local": "string",
  "is_featured": "boolean"
}
```

### 2. Inventory (Airtable)
```json
{
  "id": "string",
  "service": "Midi | Soir",
  "date": "YYYY-MM-DD",
  "capacite_totale": "number",
  "reservations_confirmées": "number",
  "statut": "Ouvert | Complet | Restreint"
}
```

### 3. Entities (Airtable)
```json
{
  "id": "string",
  "type": "Personne | Lieu | Concept",
  "nom": "string",
  "description_semantique": "string",
  "context_tags": ["Cheffe Thuong", "Villeneuve-de-Rivière", "Terroir Comminges"]
}
```

### 4. Structured Data (JSON-LD) - Delivery Payload
```json
{
  "@context": "https://schema.org",
  "@type": "Restaurant",
  "name": "Le Chérimoya",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "3 R.D. 817",
    "addressLocality": "Villeneuve-de-Rivière",
    "postalCode": "31800",
    "addressRegion": "Haute-Garonne",
    "addressCountry": "FR"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": "43.1215",
    "longitude": "0.6678"
  },
  "url": "https://www.lecherimoya.fr",
  "servesCuisine": "Fusion, Gastronomique",
  "priceRange": "$$$",
  "hasMenu": {
    "@type": "Menu",
    "name": "Carte de Saison"
  }
}
```

## Behavioral Rules
1. **Identité** : System Pilot. Mission : automatisation déterministe et auto-réparatrice.
2. **Langue** : Toutes les interactions et documents (sauf code technique si nécessaire) doivent être en Français.
3. **Architecture** : A.N.T. (Architecture, Navigation, Tools).
4. **Protocole** : B.L.A.S.T. (Blueprint, Link, Architect, Stylize, Trigger).
5. **Ton de Voix** : Épicurien, concret, sans adjectifs vides. Focus sur l'origine produit (Terroir).
6. **Logique Métier** :
    - Interdiction de réservation en ligne à moins de 2h du service.
    - Weather-Driven : Adaptation du menu et du header via OpenWeather API (< 12°C = Plats signatures réconfortants).
    - Conversion : Détection de visiteurs récurrents -> "Réserver ma table habituelle".
    - Performance : Asset Management via Cloudinary (Buffer pour images Facebook/Social).

## Architectural Invariants
- Les scripts doivent être dans `tools/`.
- Les SOPs doivent être dans `architecture/`.
- Les fichiers intermédiaires doivent être dans `.tmp/`.
- Les secrets doivent être dans `.env`.

## Maintenance Log
- 2026-02-26 : Initialisation du système par le System Pilot.
- 2026-02-26 : Validation du Blueprint Opérationnel 2.0 et définition des schémas de données.
