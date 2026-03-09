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

### Côté Administrateur (Dashboard & Control Center)

- **Gestion du Parcours Client** : Confirmation, refus ou annulation des réservations avec envoi de mail automatique d'un simple clic.
- **Réservation Manuelle Avancée** : Formulaire optimisé avec sélection de créneaux horaires dynamiques (intervalles de 15 min adaptés au service Midi/Soir).
- **Control Center Temps Réel** : Vue par service (Midi/Soir) avec visibilité totale sur les réservations confirmées et en attente, permettant une gestion fluide directement depuis la salle.
- **Interface Premium & Responsive** : Design soigné avec charte graphique "Vibe" (accent color #cfa86e), typographie moderne et support complet du mode sombre.
- **Gestion Complète du Menu (CRUD)** : Ajouter, Modifier, et Supprimer les plats en temps réel.
- **Upload & Recadrage d'Images** : Intégration de Cropper.js et hébergement optimisé sur Cloudinary.
- **Engine de Génération d'Images (IA)** : Intégration de Google Gemini Image Generation pour créer des visuels gastronomiques sur-mesure.
- **Batch Image Sync (`tools/batch_update_images.py`)** : Script de synchronisation automatisé pour l'import massif des visuels vers Cloudinary.

## 🛠️ Stack Technique

- **Frontend** : HTML5, Vanilla CSS (Premium Design System), JS natif, Cropper.js.
- **Backend** : Python 3 / Flask / BookingManager (Logique métier complexe).
- **IA Gėnérative** : Google Gemini (Images, SEO & Analyse de données).
- **Bases de Données** : Airtable (Architecture A.N.T. : Architecture, Navigation, Tools).
- **Images & Assets** : Cloudinary (Transformation à la volée `f_auto,q_auto`).
- **Météo** : OpenWeather API (Weather-Driven UI).

## ⚙️ Maintenance & Évolutions

- **Optimisation Navigation & Réservation (09/03/2026)** :
  - **Refonte Navigation Mobile** : Généralisation de l'**API History** (`pushState` / `popstate`) sur l'ensemble de l'écosystème (site public, Hub, Dashboard). L'expérience "Bouton Retour" est désormais infaillible, y compris pour les confirmations de suppression et le recadrage d'images.
  - **Réservation Dynamique** : Implémentation de la règle métier "Délai de 2h" (calculé en temps réel) et passage à des créneaux de 15 minutes pour une gestion plus fine du flux client.
  - **Synchronisation UI** : Alignement complet des fonctionnalités de réservation entre le site public et le Hub d'administration.
- **Optimisation Navigation Android (06/03/2026)** :
  - Intégration initiale de l'**API History** sur les modales principales.
  - Correction du bug crash "Bouton Retour".
- **Optimisation Réservations (04/03/2026)** :
  - Refonte de la visibilité dans le Control Center : toutes les réservations du jour (y compris les saisies manuelles en attente) sont désormais immédiatement visibles.
  - Implémentation des boutons d'action rapide : Confirmer, Refuser ou Annuler en un clic avec demande de confirmation sécurisée.
  - Correction du rendu des listes déroulantes (Select) en mode sombre pour une lisibilité parfaite.
- **Maintenance du Menu (02/03/2026)** :
  - Nettoyage de la base Airtable et intégration de 16 nouveaux visuels HD.
  - Consolidation de la logique de résolution d'images (Cloudinary vs Airtable).
- **Automation** : Le script `tools/batch_update_images.py` reste l'outil privilégié pour synchroniser les nouveaux plats.

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

## 🔐 Sécurité & Administration

L'accès au Dashboard est sécurisé par **Google OAuth2**.
Seul l'email administrateur défini (`lecherimoyarestaurant@gmail.com`) est autorisé à se connecter.

**Identifiants requis dans le `.env` pour l'admin :**

- `GOOGLE_CLIENT_ID` : Obtenu sur Google Cloud Console.
- `GOOGLE_CLIENT_SECRET` : Obtenu sur Google Cloud Console.
- `FLASK_SECRET_KEY` : Clé de session sécurisée.

---
*Projet propulsé par l'IA (Vibe Coding) pour Le Chérimoya - 2026. Design & Code optimisés pour la conversion et l'expérience utilisateur premium.*
