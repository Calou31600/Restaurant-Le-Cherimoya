# Restaurant Le Chérimoya - Site & Dashboard Administrateur

Bienvenue dans le dépôt du site vitrine et de l'interface d'administration du **Restaurant Le Chérimoya**, situé au **3 R.D. 817, 31800 Villeneuve-de-Rivière**. Ce projet full-stack propose une expérience utilisateur moderne pour les clients et un outil complet et intuitif pour la gestion de la carte du restaurant.

📞 **Contact & Réservation** : 07 56 09 47 24


## 🌟 Fonctionnalités Principales

### Côté Client (Site Public)
- **Menu Dynamique** : Affichage des plats triés par catégories (Entrées, Plats, Desserts, etc.) et par ordre alphabétique.
- **Menu Bilingue (Français/Anglais)** : Support multilingue pour l'affichage des plats et de leurs descriptions.
- **Gestion des Allergènes** : Affichage conditionnel et intelligent d'icônes (Lactose, Gluten, Cacahuéte) permettant de repérer au premier coup d'œil les plats ciblés.
- **Recommandations Météo (IA)** : Une bannière météo s'affiche en fonction de la température actuelle du restaurant et met en avant les plats les plus réconfortants ou rafraîchissants.
- **Système de Réservation Intelligent** : Formulaire intégré avec vérification en temps réel des disponibilités et respect de la "règle des 2 heures".
- **Automatisations Emails** : Envoi automatique d'e-mails de notification au restaurant pour chaque nouvelle demande, et e-mails de confirmation/annulation envoyés aux clients d'un simple clic depuis l'interface admin.
- **Avis Google Dynamiques** : Récupération automatique de la note, du nombre d'avis et des commentaires clients via l'API Google Places.
- **Optimisation SEO, AEO & GEO** : Implémentation du format JSON-LD, balises sémantiques, et Meta Tags pour une visibilité maximale.

### Côté Administrateur (Dashboard)
- **Gestion du Parcours Client** : Confirmation ou refus des réservations avec envoi de mail automatique.
- **Gestion Complète du Menu (CRUD)** : Ajouter, Modifier, et Supprimer les plats en temps réel.
- **Upload & Recadrage d'Images** : Intégration de Cropper.js et hébergement optimisé sur Cloudinary.
- **Gestion de l'Inventaire** : Synchronisation des tables `Disponibilites` et `Reservations` pour éviter le surbooking.
- **Engine de Génération d'Images (IA)** : Un outil de génération d'images haute qualité (Gemini Image Generation) a été intégré pour assurer une couverture à 100% des visuels du menu.
- **Batch Image Sync** : Script d'automatisation (`tools/batch_update_images.py`) pour l'upload groupé vers Cloudinary et la synchronisation avec Airtable.

## 🛠️ Stack Technique

- **Frontend** : HTML5, Vanilla CSS, JS natif.
- **Backend** : Python 3 / Flask.
- **Bases de Données** : Airtable (Tables : `Dynamic_Menu`, `Disponibilites`, `Reservations`).
- **Images** : Cloudinary.
- **Notifications** : SMTP Gmail (Automatisations emails).
- **Météo** : OpenWeather API.

## ⚙️ Installation & Lancement en local

1. **Cloner le dépôt** :
   ```bash
   git clone https://github.com/Calou31600/Restaurant-Le-Cherimoya.git
   cd "Restaurant Le Cherimoya"
   ```

2. **Installation** :
   ```bash
   pip install -r requirements.txt
   ```

3. **Variables d'Environnement (.env)** :
   ```env
   AIRTABLE_API_KEY=votre_pat_token
   AIRTABLE_BASE_ID=votre_base_id
   CLOUDINARY_URL=votre_url_cloudinary
   SMTP_USER=email_du_restaurant
   SMTP_PASS=mot_de_passe_application_google
   OPENWEATHER_API_KEY=votre_clef
   ```

4. **Scripts de maintenance (tools/)** :
   - `audit_airtable.py` : Vérifie l'intégrité de la carte.
   - `setup_full_airtable.py` : Configure automatiquement les tables de réservation.
   - `check_missing_photos.py` : Identifie les plats sans images.

## 🔐 Sécurité & Administration
L'accès au Dashboard est sécurisé par **Google OAuth2**.
Seul l'email administrateur défini (`lecherimoyarestaurant@gmail.com`) est autorisé à se connecter.

**Identifiants requis dans le `.env` pour l'admin :**
- `GOOGLE_CLIENT_ID` : Obtenu sur Google Cloud Console.
- `GOOGLE_CLIENT_SECRET` : Obtenu sur Google Cloud Console.
- `FLASK_SECRET_KEY` : Une clé aléatoire pour sécuriser les sessions.

---
*Projet propulsé par l'IA (Vibe Coding) pour Le Chérimoya - 2026. Design & Code optimisés pour la conversion et l'expérience utilisateur premium.*
