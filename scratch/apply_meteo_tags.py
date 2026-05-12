"""Applique les tags_meteo à chaque plat de Dynamic_Menu via Airtable.

Logique (cf architecture/sop_weather_logic.md) :
- Chaud  : plats/boissons frais, peu cuits, rafraîchissants (servis quand il fait chaud dehors)
- Froid  : plats chauds, rôtis, sauces, comfort food (servis quand il fait froid)
- Pluie  : comfort food, plats en sauce, sucrés réconfortants (servis sous la pluie)

Un plat peut avoir 0..3 tags. Les items très neutres (eau plate) restent sans tag.
"""
import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE = "Dynamic_Menu"
URL = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE}"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json; charset=utf-8",
}

# rec_id -> liste de tags (parmi Chaud / Froid / Pluie)
MAPPING = {
    # --- Boissons ---
    "rec07BJbMhlM9fewy": ["Chaud"],            # Sunset Boulevard (cocktail fruité)
    "rec18vMS5ZoVtrYE1": ["Chaud"],            # Schweppes (tonic)
    "rec4wdsL9ChH2nCiL": ["Chaud"],            # Lipton pêche (thé glacé)
    "rec6Z3YmgkX7ONHgx": ["Chaud"],            # Jus de litchi
    "rec8KO9C9HIkXhABV": ["Chaud"],            # Crème Lait Brun (frais et velouté)
    "recCLdBE6yriPTS4O": ["Froid", "Pluie"],   # Café au lait (chaud, réconfortant)
    "recIRk29pjg9lLyvm": ["Chaud"],            # Perrier
    "recOKe041y5q6ZcJr": ["Chaud"],            # Yaourt Battu Glacé (rafraîchissant)
    "recOU07zOMIfKRqlx": ["Chaud"],            # Mojito (frais, rafraîchissant)
    "recQDiDHbFBtZbQuu": ["Chaud"],            # Jus de mangue
    "recTHb0Z3jKXT7oQf": ["Chaud"],            # Jus d'orange
    "recWVnjFBttbsr92a": [],                   # Eau minérale (neutre)
    "recX4GmfHd2Isfpus": ["Chaud"],            # San Pellegrino
    "recZK3aO10qaTtf0Z": ["Chaud"],            # Fanta
    "recbasRfc8fP22fOZ": ["Chaud"],            # Café Glacé Vietnamien (rafraîchissant)
    "recbov7sQMxiVc9aG": ["Chaud"],            # 7up
    "recciI0Dj9zlVZRI4": ["Froid", "Pluie"],   # Thé à la menthe (chaud)
    "recdbmlFebaLhNHyA": ["Chaud"],            # Paradis Asiatique (rafraîchissant)
    "receellDX9YakJu4B": ["Chaud"],            # Piña Colada (tropical)
    "recgZZme6VG4ml7D2": ["Chaud"],            # Nuage Sucré d'Orient (rafraîchissant)
    "recmneKnOSxxoqQlR": ["Froid", "Pluie"],   # Thé noir (chaud)
    "recnvM4HValLCmLuO": ["Froid", "Pluie"],   # Infusion camomille (chaud)
    "reco4ogHhWCD5aixv": ["Chaud"],            # Americano (rafraîchissant)
    "recoNiwfr36ktJ9B1": ["Chaud"],            # Jus d'ananas
    "recsN6xsXhLy6AMbw": ["Chaud"],            # Bière Saigon (servie fraîche)
    "recslAOnunO3Tu3kC": ["Chaud"],            # Bière pression (servie fraîche)
    "rectUYXudqhxrSZ0s": ["Chaud"],            # Eau de coco
    "recxuly1QhlP94C03": ["Chaud"],            # Citron Rafraîchissant

    # --- Entrées ---
    "rec9uECFgA4c8QXZw": ["Chaud"],            # Brise Tahitia (cocktail crevettes, fraîcheur marine)
    "recLZtoE3k1H2MfH0": ["Chaud"],            # Salade Burrata (jeunes pousses, fraîche)
    "recgj3qPuPoFwpe5a": ["Chaud"],            # Salade Croquante au Nem (vinaigrette légère, jeunes pousses)
    "recp82KirGD3IpBpL": ["Chaud"],            # Coleslaw maison (salade fraîche, rafraîchissante)
    "reczvvD9T8nax2dI7": ["Chaud"],            # Brise d'Asie au soleil (velouté glacé)

    # --- À Partager ---
    "recFMbYba1ofJt4OH": ["Froid", "Pluie"],   # Gyoza croustillants (frits, chauds)
    "reckf1JkSTtcpCkm8": ["Froid", "Pluie"],   # Mini Cabécou Fondant (rôti au miel, fondant)
    "recxkfpwtckrfeFkN": ["Froid", "Pluie"],   # Nems croustillants (frits, chauds)
    "rectQDZwE2m4wyDyb": ["Froid", "Pluie"],   # Assiette fromages charcuteries (cozy, convivial)

    # --- Côté Terre ---
    "rec3zhPZQhndsPBj8": ["Froid", "Pluie"],   # Entrecôte 250gr (grillée, frites - comfort)
    "rec5e8ikOf7b4BafH": ["Chaud"],            # Tataki de Bœuf (saignant, finement tranché)
    "recPItxvyBCXxdhZh": ["Froid", "Pluie"],   # Éclats de Poulet (sauté caramel - chaud)
    "recSj9IbylI0UsjJW": ["Froid", "Pluie"],   # Poulet Rôti Crème d'Herbes (rôti, purée)
    "recczq7vid7NwRgNI": ["Froid", "Pluie"],   # Bœuf Sauté en Dés (sauce asiatique chaude)
    "receOpi8vgvBtWA5J": ["Froid", "Pluie"],   # Porc Rôti Éclats de Noix (rôti, vin rouge)
    "recjsCgaw7OZdlLq7": ["Froid", "Pluie"],   # Joue de Bœuf Confite (braisée, mijotée - winter)
    "reckoT1H11OfENaXZ": ["Froid", "Pluie"],   # Agneau Sublime (rôti, purée)
    "recwsP7GLzVt7LTrF": ["Chaud"],            # Bœuf Vermicelles Frais (nouilles fraîches, légumes croquants)
    "recy6I3fRUm1ClATC": ["Froid", "Pluie"],   # Tranches Magret Caramélisé (canard, vin rouge)

    # --- Côté Mer ---
    "recBK9Gai9eQqTfE3": ["Chaud"],            # Tataki de Saumon (saisi mais tendre rosé)
    "recLjlqgvdL9ftN2m": ["Froid", "Pluie"],   # Gambas Sautées Beurre Ail (chaud, parfumées dorées)
    "recNjmSJhb3sMuPtX": ["Froid", "Pluie"],   # Pavé Saumon Maison (rôti, sauce onctueuse vin blanc)
    "recOGJsa4ILvKz9e6": ["Chaud"],            # Flamme de Gambas Brochette (grillée - vibe été BBQ)
    "recppYpMnXzbM5ymG": ["Chaud"],            # Délice de Limande (poisson fin, salade de saison)

    # --- Formules ---
    "recJu6z09WW6nRB6R": ["Froid", "Pluie"],   # Escalope poulet panée Enfant (panée, frites)
    "recO9bLnt0nB0kue7": ["Froid", "Pluie"],   # Hamburger Enfant (frites - comfort)
    "recvn88fpSiJJflKy": ["Froid", "Pluie"],   # Nouilles sautées poulet (chaudes)
    "reczF0Qne31PQOBsQ": ["Froid", "Pluie"],   # Nouilles sautées bœuf (chaudes)

    # --- Douceurs ---
    "rec2RILi19QS3v9ap": ["Froid", "Pluie"],   # Merveilleux Chocolat Noir (chocolat, comfort)
    "recAHzzXYYPJwraim": ["Chaud"],            # Glaces au Choix
    "recJpsVbDPSvg2beh": ["Froid", "Pluie"],   # Crème Brûlée (cozy classic)
    "recKkGtPFSi73CrS3": ["Froid", "Pluie"],   # Mystérieux Parfum Café (mousse café)
    "recduqPxYxviliQn4": ["Froid", "Pluie"],   # Tiramisu au café (crémeux cozy)
    "reciN7dA775SvNTgM": ["Froid", "Pluie"],   # Tartelette Pommes Caramélisées (caramélisées, fondantes)
    "recvRJWzDye0Zp3m2": ["Froid", "Pluie"],   # Bavarois Individuel (caramel, crème)
}


def patch_batch(records):
    """PATCH up to 10 records at a time."""
    body = json.dumps({"records": records, "typecast": True}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(URL, data=body, method="PATCH", headers=HEADERS)
    res = urllib.request.urlopen(req)
    return json.loads(res.read().decode("utf-8"))


def main():
    records = [
        {"id": rec_id, "fields": {"tags_meteo": tags}}
        for rec_id, tags in MAPPING.items()
    ]
    print(f"Patching {len(records)} records in batches of 10...")
    summary = {"Chaud": 0, "Froid": 0, "Pluie": 0, "Sans tag": 0}
    for tags in MAPPING.values():
        if not tags:
            summary["Sans tag"] += 1
        for t in tags:
            summary[t] = summary.get(t, 0) + 1
    print("Distribution prévue :", summary)

    for i in range(0, len(records), 10):
        batch = records[i:i + 10]
        result = patch_batch(batch)
        print(f"  Batch {i // 10 + 1} : {len(result.get('records', []))} OK")
    print("Done.")


if __name__ == "__main__":
    main()
