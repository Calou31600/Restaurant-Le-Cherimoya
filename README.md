# Restaurant Le Chérimoya - Site & Dashboard Administrateur

Bienvenue dans le dépôt du site vitrine et de l'interface d'administration du **Restaurant Le Chérimoya**, situé au **3 R.D. 817, 31800 Villeneuve-de-Rivière**. Ce projet full-stack propose une expérience utilisateur moderne pour les clients et un outil complet et intuitif pour la gestion de la carte du restaurant.

📞 **Contact & Réservation** : 07 56 09 47 24


## 🌟 Fonctionnalités Principales

### Côté Client (Site Public)
- **Menu Dynamique** : Affichage des plats triés par catégories (Entrées, Plats, Desserts, etc.) et par ordre alphabétique.
- **Menu Bilingue (Français/Anglais)** : Support multilingue pour l'affichage des plats et de leurs descriptions.
- **Gestion des Allergènes** : Affichage conditionnel et intelligent d'icônes (Lactose, Gluten, Cacahuéte) permettant de repérer au premier coup d'œil les plats ciblés.
- **Recommandations Météo (IA)** : Une bannière météo s'affiche en fonction de la température actuelle du restaurant et met en avant les plats les plus réconfortants ou rafraîchissants.
- **Système de Réservation** : Formulaire intégré permettant de choisir la date, le nombre de couverts, le service (Midi/Soir) et l'horaire.
- **Optimisation SEO, AEO & GEO** : Implémentation du format JSON-LD, de balises sémantiques HTML5, Open Graph, Meta descriptions engageantes, Sitemap et Robots.txt pour une parfaite visibilité et compréhension par les moteurs de recherche et IA génératives.
- **Design Premium** : Interface élégante avec mode sombre (Dark Mode) et effet "Glassmorphism".
- **Responsive** : Parfaitement adapté à toutes les tailles d'écrans (Mobile, Tablette, Desktop).

### Côté Administrateur (Dashboard)
- **Gestion Complète du Menu (CRUD)** : Ajouter, Modifier, et Supprimer les plats en temps réel.
- **Catégories & Tags Météo** : Affecter directement des tags (Chaud, Froid) et des catégories (À Partager, Côté Mer, etc.) à chaque plat.
- **Upload & Recadrage d'Images** : Intégration de Cropper.js pour recadrer les images (format 4:3) avant le téléchargement sur Cloudinary.
- **Modales de Sécurité** : Fenêtre de confirmation de suppression nativement intégrée au design du site.
- **Système de Cache** : La majorité des requêtes sont mises en cache pour garantir des temps de chargements optimaux, et le cache est purgé dynamiquement lors de toute modification.

## 🛠️ Stack Technique

- **Frontend** : HTML5, Vanilla CSS (Variables, Flexbox/Grid), JavaScript natif (Fetch API).
- **Backend** : Python 3 avec [Flask](https://flask.palletsprojects.com/).
- **Base de Données** : [Airtable](https://airtable.com/). Le site est synchronisé avec une table `Dynamic_Menu`.
- **Hébergement Images** : [Cloudinary](https://cloudinary.com/).
- **API Météo** : [OpenWeather API](https://openweathermap.org/) pour la météo en temps réel de Villeneuve-de-Rivière.

## ⚙️ Installation & Lancement en local

1. **Cloner le dépôt** :
   ```bash
   git clone <url-du-repo>
   cd "Restaurant Le Cherimoya"
   ```

2. **Créer un environnement virtuel (optionnel mais recommandé)** :
   ```bash
   python -m venv venv
   source venv/Scripts/activate # Sur Windows
   ```

3. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

4. **Variables d'Environnement** :
   Créez un fichier `.env` à la racine du projet et ajoutez vos clés secrètes :
   ```env
   LOG_LEVEL=INFO
   OPENWEATHER_API_KEY=votre_clef_openweather
   CLOUDINARY_URL=votre_url_cloudinary
   AIRTABLE_API_KEY=votre_api_key_airtable
   AIRTABLE_BASE_ID=votre_base_id_airtable
   CACHE_TIMEOUT=3600
   RESTAURANT_LAT=43.1215
   RESTAURANT_LON=0.6678
   ```

5. **Lancer le serveur de développement** :
   ```bash
   python app.py
   ```
   Le site sera accessible sur `http://localhost:5000` et l'administration sur `http://localhost:5000/admin`.

## 🚀 Déploiement (Vercel)

L'application est configurée pour un déploiement serveur-less (Serverless) sur **Vercel** via le fichier `vercel.json` intégré :
1. Connectez votre compte GitHub à Vercel.
2. Importez ce dépôt.
3. Configurez toutes les variables d'environnement (`OPENWEATHER_API_KEY`, `CLOUDINARY_URL`, `AIRTABLE_API_KEY`, `AIRTABLE_BASE_ID`, etc.) dans les paramètres d'environnement de Vercel.
4. Le déploiement se fait automatiquement via la commande de build et le script `tools/main_engine.py` en tant que point d'entrée.

## 🔒 Sécurité
- Le backend valide minutieusement les requêtes venant du dashboard.
- Modale de sécurité prévenant toute suppression accidentelle de la base de données Airtable.
- Aucune donnée env sensible n'est archivée sur Git. Le fichier `.env` est exclu via le `.gitignore`.

---
*Projet propulsé et structuré par IA (Vibe Coding) et maintenu pour Le Chérimoya.*