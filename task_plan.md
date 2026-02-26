# Tasks Plan - Restaurant Le Cherimoya

## Phase 0: Initialisation ✅
- [x] Créer les fichiers de base (`task_plan.md`, `findings.md`, `progress.md`, `gemini.md`)
- [x] Définir le schéma de données dans `gemini.md` (Blueprint 2.0 validé)

## Phase 1: Blueprint (Vision & Logique) ✅
- [x] Analyse des besoins et objectifs (North Star : Plateforme Smart-Premium)
- [x] Identification des intégrations (OpenWeather, Cloudinary, Airtable, n8n, Zenchef/GCal, GBP, WhatsApp)
- [x] Stratégie SEO/GEO/AEO définie

## Phase 2: Link (Connectivité) ⏳
- [ ] Créer le fichier `.env` avec les placeholders pour :
    - AIRTABLE_API_KEY / BASE_ID
    - OPENWEATHER_API_KEY
    - CLOUDINARY_URL
    - WHATSAPP_API_TOKEN
- [ ] **Tests de Connexion (Scripts tools/)** :
    - `test_airtable.py` : Vérifier l'accès aux tables [Dynamic_Menu], [Inventory], [Entities]
    - `test_weather.py` : Vérifier la récupération des données météo pour Villeneuve-de-Rivière
    - `test_cloudinary.py` : Vérifier l'accès au CDN

## Phase 3: Architect (Structure A.N.T.)
- [ ] **Layer 1: Architecture (SOPs)** :
    - `sop_weather_logic.md` : Algorithme de changement de menu selon T° et conditions.
    - `sop_booking_rules.md` : Gestion de la fenêtre de 2h et synchronisation Inventory.
    - `sop_content_generation.md` : Directives pour GEO/AEO/SEO.
- [ ] **Layer 3: Tools (Scripts)** :
    - `sync_fb_cloudinary.py` : Aspirer images FB -> Cloudinary.
    - `weather_engine.py` : Fetch météo -> Output JSON pour Frontend.
    - `booking_manager.py` : Interface de réservation avec logique de protection.

## Phase 4: Stylize (Refinement & UI)
- [ ] Génération du JSON-LD structuré dynamique.
- [ ] Design du Header Adaptatif (CSS/JS) selon la météo.
- [ ] Implémentation du bouton "Table habituelle".

## Phase 5: Trigger (Déploiement)
- [ ] Setup n8n workflows.
- [ ] Transfert cloud et configuration WhatsApp triggers.
- [ ] Maintenance Log final.
