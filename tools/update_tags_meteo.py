"""
Mise a jour intelligente des tags_meteo pour chaque plat dans Airtable.
Logique :
  - "Froid"  : Plats reconfortants, chauds, mijotes, riches (on les met en avant quand il fait froid)
  - "Chaud"  : Plats legers, frais, salades, fruits de mer legers, boissons fraiches, glaces
  - "Pluie"  : Plats ultra-reconfortants, cocooning (sous-ensemble du Froid, les vrais comfort foods)
"""

import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}
TABLE_NAME = "Dynamic_Menu"
BASE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME}"

# Mapping precis : nom du plat -> tags_meteo
TAGS_METEO = {
    # === ENTREES ===
    "Salade de poulet croustillant":        ["Chaud"],           # Salade fraiche
    "Salade de camembert roti":             ["Froid", "Pluie"],  # Camembert chaud = reconfortant
    "Siu mai vapeur 5pc":                   ["Froid", "Pluie"],  # Bouchees vapeur = chaleur
    "Salade de nems":                       ["Chaud"],           # Salade = fraicheur
    "Ha Kao aux crevettes 5 pc":            ["Froid", "Pluie"],  # Vapeur = reconfortant

    # === A PARTAGER ===
    "4 nems poulet croustillants":          ["Chaud", "Froid"],  # Passe-partout, croustillant
    "Plateau de fromages mixtes":           ["Froid"],           # Fromages = soiree fraiche
    "Assiette de charcuterie et fromages":  ["Froid"],           # Charcuterie = soiree fraiche

    # === COTE TERRE ===
    "Poulet sauce teriyaki":                ["Chaud"],           # Grille, leger avec riz
    "Faux filet de boeuf 250gr":            ["Froid"],           # Viande rouge = reconfortant
    "Tataki de boeuf 250gr":                ["Chaud", "Froid"],  # Mi-cuit, leger mais riche
    "Filet de canard sauce fait maison":    ["Froid"],           # Canard = automne/hiver
    "Filet de canard sauce caramel balsamique": ["Froid", "Pluie"], # Sauce onctueuse = cocooning
    "Joue de boeuf confite au four":        ["Froid", "Pluie"],  # Mijote 7h = ultimate comfort
    "Filet de poulet au cheddar":           ["Froid", "Pluie"],  # Fromage fondu = reconfortant
    "Cotes d'agneau grilles aux herbes":    ["Froid"],           # Agneau grille = hiver
    "Cote de boeuf 400g":                   ["Froid"],           # Grosse piece = soiree fraiche

    # === COTE MER ===
    "Crevettes sautees beurre ail":         ["Chaud"],           # Crevettes legeres
    "Saumon sauce teriyaki":                ["Chaud", "Froid"],  # Poisson grille, polyvalent
    "Grosses gambas grillees 3pc":          ["Chaud"],           # Gambas = ete, soleil
    "Moules a la creme beurre":             ["Froid", "Pluie"],  # Moules-frites = comfort
    "Pates aux fruits de mer":              ["Froid", "Pluie"],  # Pates chaudes = reconfortant
    "Riz saute aux fruits de mer":          ["Chaud"],           # Riz saute = leger, asiatique
    "Assiette de fruits de mer":            ["Chaud"],           # Fruits de mer = fraicheur
    "Filet de bar au beurre":               ["Chaud"],           # Poisson leger

    # === DOUCEURS ===
    "Tartelette tatin":                     ["Froid", "Pluie"],  # Tarte chaude caramelisee
    "Poire en trompe-l'oeil":               ["Chaud"],           # Mousse fraiche
    "Tropezienne":                          ["Chaud"],           # Brioche = ete, sud
    "Dome rubis":                           ["Chaud"],           # Mousse framboise = fraicheur
    "Tiramisu au cafe":                     ["Froid", "Pluie"],  # Cafe + mascarpone = cocooning
    "Creme Brulee au Cafe":                 ["Froid",  "Pluie"], # Creme chaude = reconfort
    "Glaces (2 boules au choix)":           ["Chaud"],           # Glace = chaleur

    # === BOISSONS ===
    "Prohibition":                          ["Chaud"],           # Jus frais
    "Virgin mojito":                        ["Chaud"],           # Mocktail frais
    "L'exotique":                           ["Chaud"],           # Tropical = chaleur
    "Virgin colada":                        ["Chaud"],           # Coco frais
    "Le delice":                            ["Chaud"],           # Litchi frais
    "Americano":                            ["Chaud", "Froid"],  # Aperitif toute saison
    "Pina colada":                          ["Chaud"],           # Cocktail tropical
    "Sunset boulevard":                     ["Chaud"],           # Cocktail ete
    "Mojito":                               ["Chaud"],           # Cocktail frais
    "Paradis asiatique":                    ["Chaud"],           # Prosecco + hibiscus = ete
    "Nana fizz":                            ["Chaud"],           # Gin frais

    # === FORMULES ===
    "Formule Vietnamienne":                 ["Froid", "Pluie"],  # Menu complet reconfortant
    "Menu Enfant":                          [],                  # Neutre, pas de tag
}


def normalize(text):
    """Normalise un texte pour la comparaison (supprime accents courants)."""
    replacements = {
        "é": "e", "è": "e", "ê": "e", "ë": "e",
        "à": "a", "â": "a", "ä": "a",
        "ù": "u", "û": "u", "ü": "u",
        "ô": "o", "ö": "o",
        "î": "i", "ï": "i",
        "ç": "c",
        "œ": "oe",
        "'": "'",
    }
    result = text.lower()
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result


def find_tags(plat_name):
    """Trouve les tags meteo pour un plat donne, avec correspondance souple."""
    # Essai exact d'abord
    for key, tags in TAGS_METEO.items():
        if normalize(key) == normalize(plat_name):
            return tags

    # Essai partiel (le nom Airtable contient le nom du mapping ou inversement)
    for key, tags in TAGS_METEO.items():
        if normalize(key) in normalize(plat_name) or normalize(plat_name) in normalize(key):
            return tags

    return None  # Pas de correspondance


def main():
    print("Recuperation des records Airtable...")
    records = []
    url = BASE_URL
    while True:
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        if "records" in data:
            records.extend(data["records"])
        if "offset" in data:
            url = f"{BASE_URL}?offset={data['offset']}"
        else:
            break

    print(f"  {len(records)} records trouves.\n")

    updated = 0
    skipped = 0
    not_found = []

    for rec in records:
        plat = rec["fields"].get("Plat", "???")
        rec_id = rec["id"]
        current_tags = rec["fields"].get("tags_meteo", [])
        new_tags = find_tags(plat)

        if new_tags is None:
            not_found.append(plat)
            print(f"  [?] {plat} -- pas de mapping trouve")
            continue

        if set(current_tags) == set(new_tags):
            skipped += 1
            print(f"  [=] {plat} -- deja correct: {current_tags}")
            continue

        # Mise a jour
        payload = {
            "fields": {
                "tags_meteo": new_tags
            },
            "typecast": True
        }
        res = requests.patch(f"{BASE_URL}/{rec_id}", headers=HEADERS, json=payload)

        if res.status_code == 200:
            updated += 1
            print(f"  [+] {plat}: {current_tags} -> {new_tags}")
        else:
            print(f"  [!] {plat}: ERREUR {res.status_code} - {res.text}")

        time.sleep(0.25)

    print(f"\n--- Resultat ---")
    print(f"  Mis a jour : {updated}")
    print(f"  Deja OK    : {skipped}")
    if not_found:
        print(f"  Sans mapping: {len(not_found)}")
        for p in not_found:
            print(f"    - {p}")


if __name__ == "__main__":
    main()
