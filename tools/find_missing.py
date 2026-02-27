
import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = "Dynamic_Menu"
HEADERS = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}

MENU_REEL = [
    # Entrées
    {"Plat": "Salade de poulet croustillant"},
    {"Plat": "Salade de camembert roti"},
    {"Plat": "Siu mai vapeur 5pc"},
    {"Plat": "Salade de nems"},
    {"Plat": "Ha Kao aux crevettes 5 pc"},
    # À Partager
    {"Plat": "4 nems poulet croustillants"},
    {"Plat": "Plateau de fromages mixtes"},
    {"Plat": "Assiette de charcuterie et fromages"},
    # Côté Terre
    {"Plat": "Poulet sauce teriyaki"},
    {"Plat": "Faux filet de bœuf 250gr"},
    {"Plat": "Tataki de bœuf 250gr"},
    {"Plat": "Filet de canard sauce fait maison"},
    {"Plat": "Filet de canard sauce caramel balsamique"},
    {"Plat": "Joue de bœuf confite au four"},
    {"Plat": "Filet de poulet au cheddar"},
    {"Plat": "Côtes d’agneau grillés aux herbes"},
    {"Plat": "Côte de bœuf 400g"},
    # Côté Mer
    {"Plat": "Crevettes sautées beurre ail"},
    {"Plat": "Saumon sauce teriyaki"},
    {"Plat": "Grosses gambas grillées 3pc"},
    {"Plat": "Moules à la crème beurre"},
    {"Plat": "Pâtes aux fruits de mer"},
    {"Plat": "Riz sauté aux fruits de mer"},
    {"Plat": "Assiette de fruits de mer"},
    {"Plat": "Filet de bar au beurre"},
    # Desserts
    {"Plat": "Tartelette tatin"},
    {"Plat": "Poire en trompe-l'œil"},
    {"Plat": "Tropézienne"},
    {"Plat": "Dôme rubis"},
    {"Plat": "Tiramisu au café"},
    {"Plat": "Crème Brûlée au Café"},
    {"Plat": "Glaces (2 boules au choix)"},
    # Boissons
    {"Plat": "Prohibition"},
    {"Plat": "Virgin mojito"},
    {"Plat": "L'exotique"},
    {"Plat": "Virgin colada"},
    {"Plat": "Le délice"},
    {"Plat": "Américano"},
    {"Plat": "Pina colada"},
    {"Plat": "Sunset boulevard"},
    {"Plat": "Mojito"},
    {"Plat": "Paradis asiatique"},
    {"Plat": "Nana fizz"},
    # Formules
    {"Plat": "Formule Vietnamienne"},
    {"Plat": "Menu Enfant"},
]

def find_missing():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME}"
    airtable_names = []
    offset = None
    while True:
        params = {"offset": offset} if offset else {}
        res = requests.get(url, headers=HEADERS, params=params)
        data = res.json()
        airtable_names.extend([r.get("fields", {}).get("Plat") for r in data.get("records", [])])
        offset = data.get("offset")
        if not offset:
            break
            
    print(f"Total Airtable: {len(airtable_names)}")
    missing = []
    for item in MENU_REEL:
        if item["Plat"] not in airtable_names:
            missing.append(item["Plat"])
            
    if missing:
        print(f"Plats manquants dans Airtable ({len(missing)}):")
        for m in missing:
            print(f"- {m}")
    else:
        print("Toutes les fiches sont présentes !")

if __name__ == "__main__":
    find_missing()
