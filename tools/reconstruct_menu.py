
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

# Lexique et traductions récupérées fidèlement des menus photos
TRANSLATIONS = {
    "Salade de poulet croustillant": ("Crispy Chicken Salad", "Crispy chicken breast harmonized with fresh greens and homemade dressing"),
    "Salade de camembert roti": ("Baked camembert salad", "Baked camembert with honey, served with fresh greens, prosciutto and olives"),
    "Siu mai vapeur 5pc": ("5 pc Steamed siu mai", "Delicate steamed dumplings filled with tender pork and fresh shrimp, served with a sweet sauce with subtle caramelized notes."),
    "Salade de nems": ("Spring roll salad", "Crispy spring rolls harmonized with green salads and homemade dressing"),
    "Ha Kao aux crevettes 5 pc": ("5pc Shrimp Ha Kao", "Delicate steamed dumplings filled with fresh shrimp, with a fine and translucent texture, served with a lightly sweet sauce."),
    "4 nems poulet croustillants": ("4 crispy spring rolls", "Plate of crispy spring rolls, wrapped in lettuce leaves, served with traditional dipping sauce"),
    "Plateau de fromages mixtes": ("Assorted cheeses", "Cheese plate of the day, a selection of seasonal cheeses to enjoy a variety of flavors and textures."),
    "Assiette de charcuterie et fromages": ("Cold cuts and cheese platter", "A refined platter of flavourful Iberian ham, tender coppa and a selection of cheeses – perfect for sharing or as a starter."),
    "Poulet sauce teriyaki": ("Chicken breast teriyaki sauce", "Thinly sliced chicken breast skewers, grilled and topped with teriyaki sauce, served with fragrant rice and grilled vegetables"),
    "Faux filet de bœuf 250gr": ("Striploin steak", "Grilled beef entrecôte, served with homemade sauce and French fries"),
    "Tataki de bœuf 250gr": ("Beef tataki", "Tender grilled beef, thinly sliced and marinated with homemade sauce, served with mashed potatoes and grilled vegetables"),
    "Filet de canard sauce fait maison": ("Duck breast with homemade sauce", "Grilled duck breast topped with homemade sauce, served with French fries"),
    "Filet de canard sauce caramel balsamique": ("Grilled Duck Breast with Balsamic Caramel Sauce", "Grilled duck breast paired with a rich balsamic caramel sauce, served with mashed potatoes and grilled vegetables"),
    "Joue de bœuf confite au four": ("Candied beef cheeks", "Candied beef cheeks with wine, herbs and vegetables, finished with a rich sauce and served with fresh pasta"),
    "Filet de poulet au cheddar": ("Chicken breast with cheddar", "Grilled chicken breast topped with a thin layer of Cheddar, paired with homemade mushroom sauce and fresh pasta"),
    "Côtes d’agneau grillés aux herbes": ("Herb-grilled lamb chops", "Lamb chops marinated with herbs, grilled and finished with homemade sauce, served with mashed potatoes and grilled vegetables"),
    "Côte de bœuf 400g": ("Rib steak with homemade sauce", "Rib steak with homemade sauce, served with French fries and grilled vegetables"),
    "Crevettes sautées beurre ail": ("Garlic butter shrimp", "Shrimp quickly sautéed with garlic butter, served with rice and grilled vegetables"),
    "Saumon sauce teriyaki": ("Salmon with teriyaki sauce", "Grilled salmon fillet glazed with Teriyaki sauce, served with rice and grilled vegetables"),
    "Grosses gambas grillées 3pc": ("large grilled prawns 3pc", "Fresh prawns grilled with butter and garlic, served with grilled vegetables and fragrant rice"),
    "Moules à la crème beurre": ("Mussels in butter cream sauce", "Mussels sautéed in butter cream sauce, served with French fries"),
    "Pâtes aux fruits de mer": ("Seafood pasta", "Pasta cooked with shrimp, mussels, squid and homemade tomato sauce"),
    "Riz sauté aux fruits de mer": ("Seafood fried rice", "Fragrant rice with shrimp, squid, mussels, scallops and a hint of parsley"),
    "Assiette de fruits de mer": ("Seafood platter", "Gambas, shrimp, squid, and fresh mussels, scallops elegantly presented on the plate"),
    "Filet de bar au beurre": ("Lemon butter sea bass fillet", "Sea bass fillet elegantly glazed butter sauce, served with fragrant rice and grilled vegetables"),
    "Tartelette tatin": ("Tarte Tatin", "Upside-down caramelized apple tart on butter enriched with jam, served warm."),
    "Poire en trompe-l'œil": ("Pear Illusion Dessert", "Silky pear mousse with compote insert, crafted to look like a real pear."),
    "Tropézienne": ("Tropézienne Tart", "Soft brioche filled with smooth mousseline cream, lightly sweet and delicate."),
    "Dôme rubis": ("Ruby Dome", "Raspberry mousse with coulis center, on Joconde biscuit, encased in dark chocolate with ruby-red glaze. A perfect finale to your meal."),
    "Tiramisu au café": ("Coffee Tiramisu", "Coffee-soaked ladyfingers layered with creamy mascarpone, dusted with cocoa, alcohol-free."),
    "Crème Brûlée au Café": ("Coffee Crème Brûlée", "Smooth custard topped with a crisp caramel layer, delicately flavored with coffee"),
    "Glaces (2 boules au choix)": ("Ice Creams (2 scoops of your choice)", "Topped with smooth whipped cream Chantilly (vanilla, chocolate, rhum raisin, mangue, fraise, café, caramel)."),
    "Prohibition": ("Prohibition Mocktail", "Orange juice, pineapple juice, lemon, raspberry syrup"),
    "Virgin mojito": ("Virgin Mojito", "Cane sugar syrup, perrier, citron vert, menthe frais."),
    "L'exotique": ("The Exotic Mocktail", "Banana juice, passion fruit juice, apple juice, vanilla syrup, lime."),
    "Virgin colada": ("Virgin Colada", "Pineapple juice, coconut cream."),
    "Le délice": ("The Delight Mocktail", "Lychee juice, raspberry cream, lemon juice, apple juice."),
    "Américano": ("Americano", "Italian vermouth, campari bitter, perrier."),
    "Pina colada": ("Pina Colada", "Coconut cream, pineapple, white rum – a tropical cocktail, sweet and creamy"),
    "Sunset boulevard": ("Sunset Boulevard", "Orange, cranberry, peach liqueur, blackberry liqueur, vodka."),
    "Mojito": ("Mojito", "Powdered sugar, lime, Cuban rum, Perrier, angostura."),
    "Paradis asiatique": ("Asian Paradise", "Hibiscus syrup, edible hibiscus flower, lime, prosecco, lemonade."),
    "Nana fizz": ("Nana Fizz", "Gin perrier, sirop de surce de canne, citron vert, sirop de framboise."),
    "Formule Vietnamienne": ("Vietnamese Set Menu", "Starter, Main course of your choice (Shrimp or Chicken fried rice), and Dessert (Tiramisu or Crème brûlée)"),
    "Menu Enfant": ("Kids' Menu", "Main course of your choice (Crispy chicken, Beef burger, Carbonara pasta, or Teriyaki chicken) + 1 scoop of ice cream"),
}

MENU_REEL = [
    # Entrées
    {"Plat": "Salade de poulet croustillant", "desc_fr": "Filet de poulet croustillant, salade verte et sauce maison", "prix": 9.90, "Menu": ["Entrées"]},
    {"Plat": "Salade de camembert roti", "desc_fr": "Camembert roti au miel, accompagné de sa salade verte, jambon et olives", "prix": 11.90, "Menu": ["Entrées"]},
    {"Plat": "Siu mai vapeur 5pc", "desc_fr": "Délicates bouchées vapeur, farcies au porc tendre et crevettes fraîches, servie avec une sauce douce aux notes légèrement caramélisées.", "prix": 6.90, "Menu": ["Entrées", "Asie"]},
    {"Plat": "Salade de nems", "desc_fr": "Nems croustillants, salade verte et sauce maison", "prix": 9.90, "Menu": ["Entrées", "Asie"]},
    {"Plat": "Ha Kao aux crevettes 5 pc", "desc_fr": "Délicats raviolis vapeur, garnis de crevettes fraîches, à la texture fine, servis avec une sauce légèrement sucrée.", "prix": 6.90, "Menu": ["Entrées", "Asie"]},
    # À Partager
    {"Plat": "4 nems poulet croustillants", "desc_fr": "Assiette de nems croustillants, roulés dans des feuilles de salade, servis avec sauce traditionnelle.", "prix": 6.90, "Menu": ["À Partager", "Asie"]},
    {"Plat": "Plateau de fromages mixtes", "desc_fr": "Assiette de fromages du moment, une sélection de fromages de saison pour découvrir différentes saveurs et textures.", "prix": 12.90, "Menu": ["À Partager"]},
    {"Plat": "Assiette de charcuterie et fromages", "desc_fr": "Une assiette raffinée de jambon ibérique savoureux, de coppa tendre et d’une sélection de fromages – idéale à partager.", "prix": 15.90, "Menu": ["À Partager"]},
    # Côté Terre
    {"Plat": "Poulet sauce teriyaki", "desc_fr": "Blanc de poulet émincé, grillé sur brochettes et nappé de sauce teriyaki, servi avec riz parfumé et légumes grillés.", "prix": 17.90, "Menu": ["Côté Terre", "Asie"]},
    {"Plat": "Faux filet de bœuf 250gr", "desc_fr": "Faux filet de bœuf grillée, servie avec sauce maison et frites.", "prix": 18.90, "Menu": ["Côté Terre"]},
    {"Plat": "Tataki de bœuf 250gr", "desc_fr": "Bœuf grillé tendre, tranché finement et mariné avec sauce fait maison, servi avec purée de pommes de terre et légumes grillés.", "prix": 18.90, "Menu": ["Côté Terre", "Asie"]},
    {"Plat": "Filet de canard sauce fait maison", "desc_fr": "Magret de canard grillé nappé sauce fait maison, servi avec des frites.", "prix": 18.90, "Menu": ["Côté Terre"]},
    {"Plat": "Filet de canard sauce caramel balsamique", "desc_fr": "Magret de canard grillé accompagné d'une sauce caramel balsamique onctueuse, servi avec purée de pomme de terre et légumes grillés.", "prix": 18.90, "Menu": ["Côté Terre"]},
    {"Plat": "Joue de bœuf confite au four", "desc_fr": "Joue de bœuf mijotée au vin, aux herbes et légumes, nappée d’une sauce riche et servie avec pâtes fraîches.", "prix": 22.90, "Menu": ["Côté Terre"]},
    {"Plat": "Filet de poulet au cheddar", "desc_fr": "Filet de poulet grillé garni d’une fine couche de cheddar, accompagné de sauce aux champignons maison et de pâtes fraîches.", "prix": 17.90, "Menu": ["Côté Terre"]},
    {"Plat": "Côtes d’agneau grillés aux herbes", "desc_fr": "Carré d’agneau mariné aux herbes, grillé et nappé de sauce maison, servi avec purée de pommes de terre et légumes grillés.", "prix": 20.90, "Menu": ["Côté Terre"]},
    {"Plat": "Côte de bœuf 400g", "desc_fr": "Côte de bœuf, sauce maison, accompagnée de frites et de légumes grillés.", "prix": 26.90, "Menu": ["Côté Terre"]},
    # Côté Mer
    {"Plat": "Crevettes sautées beurre ail", "desc_fr": "Crevettes sautées au beurre et à l’ail, accompagnées de riz et légumes grillés.", "prix": 17.90, "Menu": ["Côté Mer"]},
    {"Plat": "Saumon sauce teriyaki", "desc_fr": "Filet de saumon grillé, nappé de sauce Teriyaki, accompagné de riz et légumes grillés.", "prix": 18.90, "Menu": ["Côté Mer", "Asie"]},
    {"Plat": "Grosses gambas grillées 3pc", "desc_fr": "Gambas fraîches grillées au beurre et à l’ail, accompagnées de légumes grillés et riz parfumé.", "prix": 29.90, "Menu": ["Côté Mer"]},
    {"Plat": "Moules à la crème beurre", "desc_fr": "Moules sautées à la sauce beurre-crème, servies avec des frites.", "prix": 16.90, "Menu": ["Côté Mer"]},
    {"Plat": "Pâtes aux fruits de mer", "desc_fr": "Pâtes cuisinées avec crevettes, moules, calamars noix de saint-jacques, et sauce tomate fait maison.", "prix": 19.90, "Menu": ["Côté Mer"]},
    {"Plat": "Riz sauté aux fruits de mer", "desc_fr": "Riz parfumé associé aux crevettes, calamars et moules, noix de saint-jacques avec une touche de persil.", "prix": 19.90, "Menu": ["Côté Mer", "Asie"]},
    {"Plat": "Assiette de fruits de mer", "desc_fr": "Gambas, crevettes, sole, calamars, moules fraîches, noix de saint-jacques, délicatement harmonisés.", "prix": 45.90, "Menu": ["Côté Mer"]},
    {"Plat": "Filet de bar au beurre", "desc_fr": "Filet de bar délicatement nappée de sauce beurre accompagnée de riz parfumé et légumes grillés.", "prix": 19.90, "Menu": ["Côté Mer"]},
    # Desserts
    {"Plat": "Tartelette tatin", "desc_fr": "Tarte renversée aux pommes caramélisées sur beurre rehaussé de confitures, servie tiède.", "prix": 4.90, "Menu": ["Douceurs"]},
    {"Plat": "Poire en trompe-l'œil", "desc_fr": "Mousse poire onctueuse with insert de compotée, façonnée comme une vraie poire.", "prix": 6.90, "Menu": ["Douceurs"]},
    {"Plat": "Tropézienne", "desc_fr": "Brioche moelleuse garnie de crème mousseline, douce et délicate.", "prix": 4.50, "Menu": ["Douceurs"]},
    {"Plat": "Dôme rubis", "desc_fr": "Mousse framboise avec coulis au cœur, sur biscuit Joconde, enrobée de chocolat noir et glaçage rouge rubis.", "prix": 7.90, "Menu": ["Douceurs"]},
    {"Plat": "Tiramisu au café", "desc_fr": "Tiramisu au café – Biscuits imbibés de café, crème mascarpone onctueuse, saupoudré de cacao, sans alcool.", "prix": 4.90, "Menu": ["Douceurs"]},
    {"Plat": "Crème Brûlée au Café", "desc_fr": "Crème onctueuse avec une fine couche de caramel croquant, parfumée au café.", "prix": 4.50, "Menu": ["Douceurs"]},
    {"Plat": "Glaces (2 boules au choix)", "desc_fr": "Glaces (2 boules au choix) surmontées de crème chantilly onctueuse.", "prix": 4.90, "Menu": ["Douceurs"]},
    # Boissons
    {"Plat": "Prohibition", "desc_fr": "Jus d'orange, jus d'ananas, citron, sirop de framboise.", "prix": 8.50, "Menu": ["Boissons"]},
    {"Plat": "Virgin mojito", "desc_fr": "Sirop de sucre de canne, perrier, citron vert, menthe frais.", "prix": 8.50, "Menu": ["Boissons"]},
    {"Plat": "L'exotique", "desc_fr": "Jus de banane, jus de maracuja, jus de pomme, sirop de vanille citron vert.", "prix": 9.50, "Menu": ["Boissons"]},
    {"Plat": "Virgin colada", "desc_fr": "Jus d'ananas, creme de coco.", "prix": 7.50, "Menu": ["Boissons"]},
    {"Plat": "Le délice", "desc_fr": "Jus de litchi, creme de framboise, jus de citron, jus de pomme.", "prix": 11.50, "Menu": ["Boissons"]},
    {"Plat": "Américano", "desc_fr": "Vermouth Italien, bitter campari, perrier.", "prix": 10.50, "Menu": ["Boissons"]},
    {"Plat": "Pina colada", "desc_fr": "Crème de coco, ananas, rhum blanc.", "prix": 9.50, "Menu": ["Boissons"]},
    {"Plat": "Sunset boulevard", "desc_fr": "Orange, cranberry, liqueur de pêche, liqueur de mûre, vodka.", "prix": 11.90, "Menu": ["Boissons"]},
    {"Plat": "Mojito", "desc_fr": "Sucre en poudre, citron vert, rhum cubain, perrier, angostura.", "prix": 10.50, "Menu": ["Boissons"]},
    {"Plat": "Paradis asiatique", "desc_fr": "Sirop d'hibiscus, fleur d'hibiscus comestible, citron vert, prosecco, limonade.", "prix": 11.50, "Menu": ["Boissons", "Asie"]},
    {"Plat": "Nana fizz", "desc_fr": "Gin perrier, sirop de surce de canne, citron vert, sirop de framboise.", "prix": 11.50, "Menu": ["Boissons"]},
    # Formules
    {"Plat": "Formule Vietnamienne", "desc_fr": "Entrée, Plat et Dessert au choix (Nems, Tiramisu, etc.)", "prix": 26.90, "Menu": ["Formules", "Asie"]},
    {"Plat": "Menu Enfant", "desc_fr": "Plat au choix (Burger, Poulet, Pâtes) + 1 boule de glace", "prix": 12.90, "Menu": ["Formules"]},
]

def clear_table():
    print("Purge de la table Airtable actuelle...")
    records = []
    url = BASE_URL
    while True:
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        if "records" in data:
            records.extend([r["id"] for r in data["records"]])
        if "offset" in data:
            url = f"{BASE_URL}?offset={data['offset']}"
        else:
            break
    if records:
        for i in range(0, len(records), 10):
            batch = records[i:i+10]
            delete_url = f"{BASE_URL}?" + "&".join([f"records[]={r}" for r in batch])
            requests.delete(delete_url, headers=HEADERS)
            time.sleep(0.3)

def populate_table():
    print(f"Reconstruction de la carte complete ({len(MENU_REEL)} plats)...")
    for i, item in enumerate(MENU_REEL):
        plat_fr = item["Plat"]
        plat_en, desc_en = TRANSLATIONS.get(plat_fr, ("", ""))
        tags_meteo = []
        if any(kw in plat_fr.lower() for kw in ["salade", "froid", "mojito", "colada", "glace"]):
            tags_meteo = ["Chaud"]
        elif any(kw in plat_fr.lower() for kw in ["vapeur", "soupe", "joue", "canard", "tatin"]):
            tags_meteo = ["Froid", "Pluie"]

        payload = {
            "fields": {
                "Plat": plat_fr,
                "Plat_EN": plat_en,
                "description_geo": item["desc_fr"],
                "description_geo_EN": desc_en,
                "tags_meteo": tags_meteo,
                "prix": item["prix"],
                "is_featured": any(kw in plat_fr.lower() for kw in ["signature", "tataki", "poire", "rubis", "gambas", "vietnamienne"]),
                "Menu": item.get("Menu", []),
                "producteur_local": "Producteur local du Terroir"
            },
            "typecast": True
        }
        res = requests.post(BASE_URL, headers=HEADERS, json=payload)
        status = "[+]" if res.status_code == 200 else "[-]"
        print(f"[{i+1}/{len(MENU_REEL)}] {status} {plat_fr}")
        if res.status_code != 200:
            print(f"    ERROR: {res.text}")
        time.sleep(0.35)

if __name__ == "__main__":
    clear_table()
    populate_table()
    print("La carte complète a été reconstituée!")
