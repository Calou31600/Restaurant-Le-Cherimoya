# 📝 Guide : Créer la table Settings dans Airtable

Ce guide vous explique comment créer manuellement la table Settings dans votre base Airtable.

## 🎯 Option 1 : Création Manuelle (Recommandé pour Vercel)

### 1. Accédez à votre base Airtable

Ouvrez votre base Airtable (celle configurée dans `AIRTABLE_BASE_ID`)

### 2. Créez une nouvelle table

1. Cliquez sur **"Add or import"** (en bas à gauche)
2. Sélectionnez **"Create empty table"**
3. Nommez la table exactement : **`Settings`**

### 3. Ajoutez les champs suivants

Pour chaque champ, cliquez sur **"+"** pour ajouter une nouvelle colonne :

#### Champs Number (Type: Number)
- `totalSeats` → **Number** (Nombre entier)
  - Description : Nombre total de places dans le restaurant
  - Valeur par défaut : 50

- `maxReservationsPerDay` → **Number** (Nombre entier)
  - Description : Nombre maximum de réservations par jour
  - Valeur par défaut : 100

- `minAdvanceBookingHours` → **Number** (Nombre entier)
  - Description : Délai minimum de réservation en heures
  - Valeur par défaut : 2

- `maxAdvanceBookingDays` → **Number** (Nombre entier)
  - Description : Délai maximum de réservation en jours
  - Valeur par défaut : 90

#### Champs Text (Type: Single line text)
- `lunchStartTime` → **Single line text**
  - Description : Heure de début du service midi (format HH:MM)
  - Valeur par défaut : 12:00

- `lunchEndTime` → **Single line text**
  - Description : Heure de fin du service midi (format HH:MM)
  - Valeur par défaut : 14:00

- `dinnerStartTime` → **Single line text**
  - Description : Heure de début du service soir (format HH:MM)
  - Valeur par défaut : 19:00

- `dinnerEndTime` → **Single line text**
  - Description : Heure de fin du service soir (format HH:MM)
  - Valeur par défaut : 22:00

#### Champ Multiple select (Type: Multiple select)
- `closedDays` → **Multiple select**
  - Description : Jours de fermeture (0=Dimanche, 1=Lundi, etc.)
  - Options à créer :
    - `0` (Dimanche)
    - `1` (Lundi)
    - `2` (Mardi)
    - `3` (Mercredi)
    - `4` (Jeudi)
    - `5` (Vendredi)
    - `6` (Samedi)

### 4. Créez un premier enregistrement

Cliquez sur **"+"** pour ajouter un nouvel enregistrement avec les valeurs par défaut :

| Champ | Valeur |
|-------|--------|
| totalSeats | 50 |
| maxReservationsPerDay | 100 |
| lunchStartTime | 12:00 |
| lunchEndTime | 14:00 |
| dinnerStartTime | 19:00 |
| dinnerEndTime | 22:00 |
| closedDays | *(laissez vide pour ouvert tous les jours)* |
| minAdvanceBookingHours | 2 |
| maxAdvanceBookingDays | 90 |

### 5. C'est terminé ! ✅

Retournez sur votre site : `https://votre-site.vercel.app/admin/settings`

Les paramètres devraient maintenant se charger et vous pourrez les modifier.

---

## 🎯 Option 2 : Script Automatique (Pour développement local)

Si vous développez en local, vous pouvez exécuter le script Python :

```bash
python tools/create_settings_table.py
```

Ce script créera automatiquement la table et l'enregistrement par défaut.

---

## 🔍 Vérification

Pour vérifier que tout fonctionne :

1. Allez sur `/admin/settings`
2. Vous devriez voir les valeurs par défaut
3. Modifiez une valeur et cliquez sur "Enregistrer"
4. Rechargez la page : vos modifications doivent être conservées

---

## ❓ Problèmes courants

### Erreur 403 ou 404
- Vérifiez que la table s'appelle exactement **`Settings`** (avec un S majuscule)
- Vérifiez que tous les champs sont bien créés avec les bons noms
- Vérifiez vos variables d'environnement sur Vercel :
  - `AIRTABLE_API_KEY`
  - `AIRTABLE_BASE_ID`

### Les paramètres ne se sauvegardent pas
- Assurez-vous qu'au moins un enregistrement existe dans la table
- Vérifiez que votre API key Airtable a les permissions d'écriture

### Les valeurs par défaut s'affichent toujours
- Vérifiez que vous avez bien créé l'enregistrement dans Airtable
- Videz le cache de votre navigateur et rechargez la page

---

## 📚 Documentation complète

Pour plus d'informations, consultez [SETTINGS_README.md](SETTINGS_README.md)
