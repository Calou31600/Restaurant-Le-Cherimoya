# Guide : Créer la table `Special_Menus_Cherimoya` dans Airtable

Cette table remplace l'ancien fichier `special_menus.json` qui ne pouvait pas
persister sur Vercel (filesystem read-only). Les événements créés depuis le
dashboard admin sont maintenant lus/écrits via Airtable.

## 1. Ouvrir la base de prod

Base : **Feuille Vierge** (`appEBQMtZMiSySoEr`).

## 2. Créer la table

1. Bouton **"+"** en bas de la liste des onglets → **"Create empty table"**
2. Nommer la table **exactement** : `Special_Menus_Cherimoya`

## 3. Ajouter les champs

Renommer le champ primaire `Name` (singleLineText) puis ajouter les suivants
dans cet ordre. **Les noms doivent être strictement identiques** (sensibles à
la casse).

| Nom du champ  | Type                | Notes                                                         |
| ------------- | ------------------- | ------------------------------------------------------------- |
| `Name`        | Single line text    | Champ primaire (déjà créé)                                    |
| `Theme`       | Single select       | Options : `noel`, `nouvel-an`, `fete-des-meres`, `saint-valentin`, `paques`, `ete`, `personnalise` |
| `Start_Date`  | Date                | Format `ISO` (`YYYY-MM-DD`) recommandé                        |
| `End_Date`    | Date                | Idem                                                          |
| `Active`      | Checkbox            | Coché = événement actif                                       |
| `Price`       | Single line text    | Ex : `75€` ou `45€ / pers.`                                   |
| `Subtitle`    | Single line text    | Sous-titre court affiché sous le nom                          |
| `Entrees`     | Long text           | Une entrée par ligne                                          |
| `Plats`       | Long text           | Un plat par ligne                                             |
| `Desserts`    | Long text           | Un dessert par ligne                                          |

> ℹ️ Les options de `Theme` se créeront automatiquement à la première
> écriture grâce à `typecast: true`, mais autant les définir tout de suite
> pour avoir un menu déroulant propre.

## 4. Vérifier

Aucune autre étape — pas de variable d'environnement à ajouter. Le code
utilise déjà `AIRTABLE_BASE_ID` et `AIRTABLE_API_KEY` comme pour les autres
tables.

Après le déploiement, créer un événement depuis `/admin/dashboard?tab=menu`
puis vérifier sur la home :

```
curl https://restaurant-le-cherimoya.vercel.app/api/special-menus/active
```

Si l'événement est *Actif* et que la date du jour est dans
`[Start_Date, End_Date]`, l'endpoint renvoie l'événement (pas `null`) et la
bannière apparaît au-dessus de la carte sur la home.
