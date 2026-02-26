# Findings - Restaurant Le Cherimoya

## Recherche & Découvertes
- Projet initialisé le 2026-02-26.
- Protocole B.L.A.S.T. activé.
- Architecture A.N.T. sélectionnée.

## Stack Technique validée
- **Orchestration** : n8n.
- **Data Source** : Airtable (Menu, Inventory, Entities).
- **Dynamic Engine** : OpenWeather API (Villeneuve-de-Rivière, 31800).
- **Asset / Performance** : Cloudinary (Buffer/CDN).
- **Booking** : Zenchef ou n8n + Google Calendar.
- **Trust** : Google Business Profile API.
- **Messaging** : WhatsApp Business API.

## Contraintes & Risques
- **Latence Sociale** : Facebook API est lente -> Cloudinary impératif pour LCP.
- **Logique 2h** : Les outils de réservation doivent refuser toute requête < 2h avant le service.
- **SEO/GEO** : Nécessité d'injection d'entités (Cheffe Thuong, Comminges) pour les moteurs génératifs.

## Coordonnées Géographiques
- Latitude : 43.1215
- Longitude : 0.6678
- CP : 31800 (Haute-Garonne)
