# Système de Paramètres du Restaurant

Ce système permet de configurer les paramètres globaux du restaurant via une interface web dans le Control Center.

## 📋 Fonctionnalités

Le système de paramètres permet de configurer :

### 🪑 Capacité
- **Nombre total de places** : Capacité maximale du restaurant
- **Réservations max par jour** : Limite de réservations quotidiennes

### 🕐 Plages Horaires
- **Service Midi** : Heure de début et fin
- **Service Soir** : Heure de début et fin

### 📅 Jours de Fermeture
- Sélection des jours de la semaine où le restaurant est fermé

### 💻 Réservation en ligne
- **Délai minimum** : Heures minimum avant une réservation
- **Délai maximum** : Jours maximum à l'avance pour réserver

## 🚀 Installation

### 1. Créer la table Airtable

Exécutez le script de création de la table Settings :

```bash
python tools/create_settings_table.py
```

Ce script va :
- Créer la table `Settings` dans votre base Airtable
- Ajouter tous les champs nécessaires
- Créer un enregistrement avec les valeurs par défaut

### 2. Vérifier la configuration

Assurez-vous que votre fichier `.env` contient :

```env
AIRTABLE_API_KEY=your_api_key
AIRTABLE_BASE_ID=your_base_id
```

## 📱 Utilisation

### Accéder aux Paramètres

1. Connectez-vous au Control Center : `/admin`
2. Cliquez sur la carte **⚙️ Paramètres**
3. Modifiez les valeurs souhaitées
4. Cliquez sur **💾 Enregistrer les paramètres**

### API Endpoints

#### GET `/api/admin/settings`
Récupère les paramètres actuels

**Réponse :**
```json
{
  "status": "success",
  "settings": {
    "totalSeats": 50,
    "maxReservationsPerDay": 100,
    "lunchStartTime": "12:00",
    "lunchEndTime": "14:00",
    "dinnerStartTime": "19:00",
    "dinnerEndTime": "22:00",
    "closedDays": [0, 1],
    "minAdvanceBookingHours": 2,
    "maxAdvanceBookingDays": 90
  }
}
```

#### POST `/api/admin/settings`
Sauvegarde les paramètres

**Body :**
```json
{
  "totalSeats": 50,
  "maxReservationsPerDay": 100,
  "lunchStartTime": "12:00",
  "lunchEndTime": "14:00",
  "dinnerStartTime": "19:00",
  "dinnerEndTime": "22:00",
  "closedDays": [0, 1],
  "minAdvanceBookingHours": 2,
  "maxAdvanceBookingDays": 90
}
```

**Réponse :**
```json
{
  "status": "success",
  "message": "Paramètres mis à jour"
}
```

## 🔧 Structure des Fichiers

```
.
├── settings.html                    # Interface web des paramètres
├── dashboard_hub.html              # Control Center (+ carte Paramètres)
├── tools/
│   ├── settings_manager.py         # Gestionnaire des paramètres
│   └── create_settings_table.py    # Script de création de table
└── app.py                          # Routes Flask
```

## 📝 Valeurs par Défaut

Si aucun paramètre n'est configuré dans Airtable, les valeurs suivantes sont utilisées :

```python
{
    "totalSeats": 50,
    "maxReservationsPerDay": 100,
    "lunchStartTime": "12:00",
    "lunchEndTime": "14:00",
    "dinnerStartTime": "19:00",
    "dinnerEndTime": "22:00",
    "closedDays": [],
    "minAdvanceBookingHours": 2,
    "maxAdvanceBookingDays": 90
}
```

## 🎨 Interface

L'interface suit le design système du restaurant avec :
- Style cohérent avec le Control Center
- Formulaire responsive (mobile-friendly)
- Messages de succès/erreur
- Validation côté client
- Design moderne avec effets glassmorphism

## 🔐 Sécurité

- Toutes les routes sont protégées par `@admin_required`
- Validation des données côté serveur
- Gestion d'erreurs complète
- Timeouts sur les requêtes Airtable

## 🐛 Résolution de Problèmes

### La table Settings n'existe pas
```bash
python tools/create_settings_table.py
```

### Erreur "Module settings_manager not found"
Vérifiez que le dossier `tools` est bien dans le `sys.path` (déjà géré dans app.py)

### Les paramètres ne se sauvegardent pas
- Vérifiez vos identifiants Airtable dans `.env`
- Consultez les logs du serveur Flask
- Vérifiez que la table Settings existe dans Airtable

## 🚀 Prochaines Étapes

Futures améliorations possibles :
- [ ] Gestion des horaires exceptionnels (jours fériés)
- [ ] Paramètres de tarification
- [ ] Temps moyen par service
- [ ] Configuration des emails
- [ ] Intégration avec le système de réservation pour appliquer les contraintes
