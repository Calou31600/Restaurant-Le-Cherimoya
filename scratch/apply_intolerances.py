"""Remplit la colonne `intolerances` de Dynamic_Menu via Airtable.

Format : multilineText, une intolérance par ligne (ex. "Lactose\nGluten").
Valeurs autorisées : Lactose, Gluten, Cacahuète.

Méthodologie (basée sur les descriptions des plats) :
- Lactose : beurre, crème, fromage, glace, chantilly, mascarpone, burrata, yaourt, lait/lait
           concentré, sauce crémeuse, purée de pommes de terre (typique avec beurre/lait).
- Gluten  : pain, panure, biscuits, pâte de tarte, fines pâtes/nouilles de blé, gyoza/nems
           (pâte de blé), bière (orge), sauce soja (présente dans sauce tataki & saveurs d'Asie).
- Cacahuète : aucun plat ne la mentionne — laissé vide.

ATTENTION : à valider manuellement. Les sauces maison et "fines pâtes" sont supposées contenir
gluten/lactose par prudence. Le cuisinier doit valider la composition exacte.
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

MAPPING = {
    # --- Boissons ---
    "rec07BJbMhlM9fewy": [],                       # Sunset Boulevard (vodka + jus, alcool)
    "rec18vMS5ZoVtrYE1": [],                       # Schweppes
    "rec4wdsL9ChH2nCiL": [],                       # Lipton pêche
    "rec6Z3YmgkX7ONHgx": [],                       # Jus de litchi
    "rec8KO9C9HIkXhABV": ["Lactose"],              # Crème Lait Brun (lait, lait concentré, crème)
    "recCLdBE6yriPTS4O": ["Lactose"],              # Café au lait
    "recIRk29pjg9lLyvm": [],                       # Perrier
    "recOKe041y5q6ZcJr": ["Lactose"],              # Yaourt Battu Glacé
    "recOU07zOMIfKRqlx": [],                       # Mojito
    "recQDiDHbFBtZbQuu": [],                       # Jus de mangue
    "recTHb0Z3jKXT7oQf": [],                       # Jus d'orange
    "recWVnjFBttbsr92a": [],                       # Eau minérale
    "recX4GmfHd2Isfpus": [],                       # San Pellegrino
    "recZK3aO10qaTtf0Z": [],                       # Fanta
    "recbasRfc8fP22fOZ": ["Lactose"],              # Café Glacé Vietnamien (lait concentré)
    "recbov7sQMxiVc9aG": [],                       # 7up
    "recciI0Dj9zlVZRI4": [],                       # Thé à la menthe
    "recdbmlFebaLhNHyA": [],                       # Paradis Asiatique (rhum + jus)
    "receellDX9YakJu4B": [],                       # Piña Colada (crème de coco = pas Lactose)
    "recgZZme6VG4ml7D2": ["Lactose"],              # Nuage Sucré d'Orient (lait, crème)
    "recmneKnOSxxoqQlR": [],                       # Thé noir
    "recnvM4HValLCmLuO": [],                       # Infusion camomille
    "reco4ogHhWCD5aixv": [],                       # Americano
    "recoNiwfr36ktJ9B1": [],                       # Jus d'ananas
    "recsN6xsXhLy6AMbw": ["Gluten"],               # Bière Saigon
    "recslAOnunO3Tu3kC": ["Gluten"],               # Bière pression
    "rectUYXudqhxrSZ0s": [],                       # Eau de coco
    "recxuly1QhlP94C03": [],                       # Citron Rafraîchissant (glace = glaçons)

    # --- Entrées ---
    "rec9uECFgA4c8QXZw": [],                       # Brise Tahitia (crevettes + sauce agrumes — pas de Lactose/Gluten typique)
    "recLZtoE3k1H2MfH0": ["Lactose"],              # Salade Burrata
    "recgj3qPuPoFwpe5a": ["Gluten"],               # Salade Croquante au Nem (nems = pâte de blé)
    "recp82KirGD3IpBpL": ["Lactose"],              # Coleslaw (sauce crémeuse)
    "reczvvD9T8nax2dI7": [],                       # Brise d'Asie au soleil (lait de coco, pas Lactose)

    # --- À Partager ---
    "recFMbYba1ofJt4OH": ["Gluten"],               # Gyoza (pâte de blé)
    "reckf1JkSTtcpCkm8": ["Lactose"],              # Mini Cabécou (chèvre)
    "recxkfpwtckrfeFkN": ["Gluten"],               # Nems (pâte souvent contient blé)
    "rectQDZwE2m4wyDyb": ["Lactose"],              # Assiette fromages charcuteries

    # --- Côté Terre ---
    "rec3zhPZQhndsPBj8": ["Lactose", "Gluten"],    # Entrecôte 250gr (sauce maison + frites souvent gluten)
    "rec5e8ikOf7b4BafH": ["Lactose", "Gluten"],    # Tataki de Bœuf (sauce tataki=soja=Gluten + purée=Lactose)
    "recPItxvyBCXxdhZh": ["Gluten"],               # Éclats de Poulet Saveurs d'Asie (sauce soja, fines pâtes)
    "recSj9IbylI0UsjJW": ["Lactose"],              # Poulet Rôti Crème d'Herbes (crème, purée)
    "recczq7vid7NwRgNI": ["Gluten"],               # Bœuf Sauté en Dés Saveurs d'Asie (sauce soja, nouilles blé)
    "receOpi8vgvBtWA5J": ["Lactose"],              # Porc Rôti Éclats de Noix (purée pdt)
    "recjsCgaw7OZdlLq7": ["Gluten"],               # Joue de Bœuf Confite (fines nouilles)
    "reckoT1H11OfENaXZ": ["Lactose"],              # Agneau Sublime (purée pdt + sauce maison)
    "recwsP7GLzVt7LTrF": ["Gluten"],               # Bœuf Vermicelles (nems + sauce maison asiatique)
    "recy6I3fRUm1ClATC": ["Gluten"],               # Tranches Magret Caramélisé (fines pâtes)

    # --- Côté Mer ---
    "recBK9Gai9eQqTfE3": ["Gluten"],               # Tataki Saumon (sauce tataki=soja + fines pâtes)
    "recLjlqgvdL9ftN2m": ["Lactose", "Gluten"],    # Gambas Sautées Beurre Ail (beurre + fines pâtes)
    "recNjmSJhb3sMuPtX": ["Lactose", "Gluten"],    # Pavé Saumon Maison (beurre + œufs + vin blanc, fines pâtes)
    "recOGJsa4ILvKz9e6": ["Lactose", "Gluten"],    # Flamme Gambas Brochette (beurre + fines pâtes)
    "recppYpMnXzbM5ymG": ["Lactose", "Gluten"],    # Délice de Limande (beurre/vin blanc + fines pâtes)

    # --- Formules ---
    "recJu6z09WW6nRB6R": ["Lactose", "Gluten"],    # Escalope panée Enfant (chapelure + glace)
    "recO9bLnt0nB0kue7": ["Lactose", "Gluten"],    # Hamburger Enfant (pain + glace)
    "recvn88fpSiJJflKy": ["Lactose", "Gluten"],    # Nouilles sautées poulet (beurre + nouilles + glace)
    "reczF0Qne31PQOBsQ": ["Lactose", "Gluten"],    # Nouilles sautées bœuf (beurre + nouilles + glace)

    # --- Douceurs ---
    "rec2RILi19QS3v9ap": ["Lactose"],              # Merveilleux Chocolat Noir (crème, glace, chantilly)
    "recAHzzXYYPJwraim": ["Lactose"],              # Glaces au Choix (+ chantilly)
    "recJpsVbDPSvg2beh": ["Lactose"],              # Crème Brûlée
    "recKkGtPFSi73CrS3": ["Lactose"],              # Mystérieux Parfum Café (mousse, glace, chantilly)
    "recduqPxYxviliQn4": ["Lactose", "Gluten"],    # Tiramisu (mascarpone + biscuits)
    "reciN7dA775SvNTgM": ["Lactose", "Gluten"],    # Tartelette Pommes (pâte + glace + chantilly)
    "recvRJWzDye0Zp3m2": ["Lactose"],              # Bavarois Individuel (crème + glace + chantilly)
}


def patch_batch(records):
    body = json.dumps({"records": records}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(URL, data=body, method="PATCH", headers=HEADERS)
    res = urllib.request.urlopen(req)
    return json.loads(res.read().decode("utf-8"))


def main():
    records = [
        {"id": rec_id, "fields": {"intolerances": "\n".join(intols)}}
        for rec_id, intols in MAPPING.items()
    ]

    counts = {"Lactose": 0, "Gluten": 0, "Cacahuète": 0, "Aucune": 0}
    for intols in MAPPING.values():
        if not intols:
            counts["Aucune"] += 1
        for i in intols:
            counts[i] = counts.get(i, 0) + 1
    print(f"Patching {len(records)} records — distribution :", counts)

    for i in range(0, len(records), 10):
        batch = records[i:i + 10]
        result = patch_batch(batch)
        print(f"  Batch {i // 10 + 1} : {len(result.get('records', []))} OK")
    print("Done.")


if __name__ == "__main__":
    main()
