# Exports Airtable → Supabase

Déposer ici les CSV exportés depuis Airtable. Le script `tools/import_from_csv.py`
les lira et insérera les données dans Supabase.

## Comment exporter depuis Airtable

Pour chaque table dans Airtable :

1. Ouvrir la table.
2. Sélectionner la vue *Grid view* (vue par défaut).
3. Cliquer sur le menu de la vue → **Download CSV**.
4. Renommer le fichier au nom canonique listé ci-dessous et le placer
   dans ce dossier.

## Fichiers attendus (noms exacts)

| Fichier CSV               | Table Airtable d'origine     | Table Supabase cible |
| ------------------------- | ---------------------------- | -------------------- |
| `Dynamic_Menu.csv`        | Dynamic_Menu                 | `menu`               |
| `Carte_Vins.csv`          | Carte_Vins                   | `wines`              |
| `Special_Menus.csv`       | Special_Menus_Cherimoya      | `special_menus`      |
| `Reservations.csv`        | Reservations                 | `reservations`       |
| `Disponibilites.csv`      | Disponibilites               | `availability`       |
| `Clients.csv`             | Clients                      | `clients`            |
| `Commandes.csv`           | Commandes                    | `commandes`          |
| `Settings_Cherimoya.csv`  | Settings_Cherimoya           | `settings`           |

Les fichiers absents sont simplement ignorés par le script — tu peux importer
une seule table à la fois.

## Exécution

```bash
# Une fois les CSV en place :
python tools/import_from_csv.py            # import simple, ajoute aux tables
python tools/import_from_csv.py --clean    # VIDE chaque table cible avant d'importer
python tools/import_from_csv.py --only menu,clients   # n'importe que ces tables
```

⚠️  `--clean` supprime toutes les lignes existantes de chaque table avant
import. À utiliser uniquement pour une ré-importation complète.

## Variables d'environnement requises

Le script lit `.env` à la racine du projet et a besoin de :

- `SUPABASE_URL`
- `SUPABASE_KEY` *(la clé publishable suffit pour INSERT/DELETE tant que RLS
  n'est pas activée. Une fois RLS en place, il faudra une `SUPABASE_SERVICE_ROLE_KEY`.)*
