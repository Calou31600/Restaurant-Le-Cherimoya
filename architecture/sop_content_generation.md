# SOP: Content Generation Strategy (SEO / GEO / AEO) (`sop_content_generation.md`)

## Objectif
Maximiser la visibilité locale (Villeneuve-de-Rivière) et la pertinence pour les moteurs de recherche et IA génératrices.

## Piliers de Contenu

### 1. GEO (Local SEO)
- **Mots-clés cibles** : "Restaurant Villeneuve-de-Rivière", "Gastronomie Comminges", "Cuisine fusion Haute-Garonne".
- **Données Structurées** : Utilisation systématique du JSON-LD `Restaurant` avec les coordonnées exactes (43.1215, 0.6678).

### 2. AEO (Answer Engine Optimization)
- Contenu structuré en Question/Réponse dans la table `Entities`.
- Focus sur l'origine des produits : "D'où viennent les produits du Chérimoya ?" -> Réponse : "Producteurs du Comminges, maraîchage local...".

### 3. SEO (Terroir & Produit)
- Chaque plat dans `Dynamic_Menu` doit avoir une `description_geo` incluant :
  - Le nom du producteur.
  - La technique culinaire (Fusion).
  - Le lien avec le terroir.

## Identité du System Pilot (Ton de Voix)
- **Épicurien** : On parle de goût, de texture, de plaisir.
- **Concret** : Pas d'adjectifs vides ("délicieux", "incroyable"). Utilisez des faits : "Agneau de 7h", "Réduction de X au poivre de Y".
- **Focus Produit** : Le produit est la star.
