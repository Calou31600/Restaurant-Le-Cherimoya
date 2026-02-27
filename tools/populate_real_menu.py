import os
import requests
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.environ.get("AIRTABLE_BASE_ID")

HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

# The table name is Dynamic_Menu
TABLE_NAME = "Dynamic_Menu"
BASE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{TABLE_NAME}"

# We will delete all records first, then insert the new ones.

def clear_table():
    print("Purge de la table Airtable actuelle...")
    records = []
    # Fetch all records
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
            
    # Delete in batches of 10
    for i in range(0, len(records), 10):
        batch = records[i:i+10]
        delete_url = f"{BASE_URL}?" + "&".join([f"records[]={r}" for r in batch])
        res = requests.delete(delete_url, headers=HEADERS)
        if res.status_code == 200:
            print(f"Supprimé {len(batch)} records.")
        else:
            print(f"Erreur purge: {res.text}")

# Dictionnaire de traduction (Standardisé pour correspondre à MENU_REEL)
TRANSLATIONS = {
    "Salade de poulet croustillant": ("Crispy Chicken Salad", "Crispy chicken fillet with fresh green salad and homemade dressing"),
    "Salade de camembert rôti": ("Roasted Camembert Salad", "Honey-roasted Camembert cheese served with leafy greens, premium cured ham, and olives"),
    "Siu mai vapeur 5pc": ("Steamed Siu Mai (5 pcs)", "Delicate steamed dumplings filled with tender pork and fresh shrimp"),
    "Salade de nems": ("Spring Rolls Salad", "Crispy golden spring rolls served with fresh salad and homemade dipping sauce"),
    "Ha Kao aux crevettes 5pc": ("Steamed Ha Kao Shrimp Dumplings (5 pcs)", "Delicate translucent steamed dumplings filled with fresh shrimp"),
    "Assiette d'apéritif - 4 nems": ("Appetizer Plate - 4 Spring Rolls", "4 crispy chicken spring rolls wrapped in fresh lettuce leaves"),
    "Plateau de fromages mixtes": ("Mixed Cheese Board", "A curated selection of seasonal cheeses to discover"),
    "Assiette de charcuterie et fromages": ("Charcuterie and Cheese Board", "Iberian ham, coppa, and a selection of premium cheeses to share"),
    "Américano": ("Americano", "Italian vermouth, bitter Campari, and sparkling water. A perfect balance of sweetness and bitterness"),
    "Pina colada": ("Pina Colada", "Coconut cream, pineapple juice, white rum. A tropical sunset in a glass"),
    "Sunset boulevard": ("Sunset Boulevard", "Orange, cranberry, peach, blackberry, and vodka. Fruity and tangy"),
    "Mojito": ("Mojito", "Cane sugar, fresh lime, Cuban rum, sparkling water, fresh mint, and Angostura bitters"),
    "Paradis asiatique": ("Asian Paradise", "Hibiscus syrup, edible hibiscus flower, lime, and Prosecco"),
    "Nana fizz": ("Nana Fizz", "Gin, sparkling water, cane sugar syrup, lime, and fresh raspberry"),
    "Prohibition (Mocktail)": ("Prohibition (Mocktail)", "Orange juice, pineapple, lemon, and raspberry syrup"),
    "Virgin mojito": ("Virgin Mojito", "Cane sugar, sparkling water, fresh lime, and mint leaves"),
    "L'exotique (Mocktail)": ("The Exotic (Mocktail)", "Banana juice, passion fruit, apple, vanilla, and lime"),
    "Virgin colada": ("Virgin Colada", "Pineapple juice and creamy coconut"),
    "Le délice (Mocktail)": ("The Delight (Mocktail)", "Lychee juice, raspberry cream, lemon, and apple"),
    "Grosses gambas grillées 3pc": ("Grilled Jumbo Prawns (3 pcs)", "Fresh prawns roasted with garlic and butter, served with grilled vegetables and fragrant rice"),
    "Moules à la crème beurre": ("Mussels in butter cream sauce", "Mussels sautéed in a rich butter-cream sauce, served with French fries"),
    "Pâtes aux fruits de mer": ("Seafood pasta", "Pasta cooked with shrimp, mussels, squid and homemade tomato sauce"),
    "Riz sauté aux fruits de mer": ("Seafood fried rice", "Fragrant rice with shrimp, squid, mussels, scallops and a hint of parsley"),
    "Assiette de fruits de mer": ("Seafood platter", "Gambas, shrimp, squid, and fresh mussels, scallops elegantly presented on the plate"),
    "Filet de bar au beurre": ("Lemon butter sea bass fillet", "Sea bass fillet elegantly glazed butter sauce, served with fragrant rice and grilled vegetables"),
    "Poulet sauce teriyaki": ("Chicken breast teriyaki sauce", "Thinly sliced chicken breast skewers, grilled and topped with teriyaki sauce, served with fragrant rice and grilled vegetables"),
    "Faux filet de bœuf 250gr": ("Striploin steak (250g)", "Grilled beef striploin steak, served with homemade sauce and French fries"),
    "Tataki de bœuf 250gr": ("Beef tataki (250g)", "Tender grilled beef, thinly sliced and marinated with homemade sauce, served with mashed potatoes and grilled vegetables"),
    "Filet de canard sauce fait maison": ("Duck breast with homemade sauce", "Grilled duck breast topped with homemade sauce, served with French fries"),
    "Filet de canard caramel balsamique": ("Grilled Duck Breast with Balsamic Caramel Sauce", "Grilled duck breast paired with a rich balsamic caramel sauce, served with mashed potatoes and grilled vegetables"),
    "Formule Vietnamienne": ("Vietnamese Set Menu", "Starter, Main Course, and Dessert of your choice (Spring Rolls, Tiramisu, etc.)"),
    "Menu Enfant": ("Kids Menu", "Main course of your choice (Burger, Chicken, Pasta) + 1 scoop of ice cream"),
    "Tartelette tatin": ("Tarte Tatin", "Upside-down caramelized apple tart on a buttery crust, enhanced with fruit jam"),
    "Poire en trompe-l'œil": ("Trompe-l'œil Pear", "Smooth pear mousse with a compote center. A magnificent signature dessert"),
    "Tropézienne": ("Tropézienne Tart", "Soft brioche filled with delicate mousseline cream"),
    "Dôme rubis": ("Ruby Dome", "Raspberry mousse, pure coulis heart, Joconde biscuit, and ruby glaze"),
    "Tiramisu au café": ("Coffee Tiramisu", "Coffee-soaked biscuits with rich mascarpone cream (alcohol-free)"),
    "Crème Brûlée au Café": ("Coffee Crème Brûlée", "Smooth coffee cream topped with a crunchy caramelized layer"),
    "Glaces (2 boules au choix)": ("Ice Cream (2 scoops)", "Flavors of your choice, served with whipped cream"),
    "Joue de bœuf braisée": ("Braised beef cheeks", "Tender beef cheeks slowly braised in a red wine reduction, served with creamy mashed potatoes and glazed carrots")
}

MENU_REEL = [
    # Entrées
    {"Plat": "Salade de poulet croustillant", "description_geo": "Filet de poulet croustillant, salade verte et sauce maison", "prix": 9.90, "tags_meteo": ["Chaud"], "is_featured": False, "Menu": ["Entrées"]},
    {"Plat": "Salade de camembert rôti", "description_geo": "Camembert rôti au miel, accompagné de sa salade verte, jambon et olives", "prix": 11.90, "tags_meteo": ["Froid", "Pluie"], "is_featured": True, "Menu": ["Entrées"]},
    {"Plat": "Siu mai vapeur 5pc", "description_geo": "Délicates bouchées vapeur, farcies au porc tendre et crevettes fraîches", "prix": 6.90, "tags_meteo": ["Pluie", "Chaud"], "is_featured": False, "Menu": ["Entrées", "Asie"]},
    {"Plat": "Salade de nems", "description_geo": "Nems croustillants, salade verte et sauce maison", "prix": 9.90, "tags_meteo": ["Chaud"], "is_featured": False, "Menu": ["Entrées", "Asie"]},
    {"Plat": "Ha Kao aux crevettes 5pc", "description_geo": "Délicats raviolis vapeur, garnis de crevettes fraîches", "prix": 6.90, "tags_meteo": ["Chaud", "Pluie"], "is_featured": False, "Menu": ["Entrées", "Asie"]},

    # Apéritifs / Tapas
    {"Plat": "Assiette d'apéritif - 4 nems", "description_geo": "4 nems poulet croustillants, roulés dans des feuilles de salade", "prix": 6.90, "tags_meteo": [], "is_featured": False, "Menu": ["À Partager", "Asie"]},
    {"Plat": "Plateau de fromages mixtes", "description_geo": "Assiette de fromages du moment, une sélection pour découvrir", "prix": 12.90, "tags_meteo": ["Froid"], "is_featured": False, "Menu": ["À Partager"]},
    {"Plat": "Assiette de charcuterie et fromages", "description_geo": "Jambon ibérique, coppa et sélection de fromages à partager", "prix": 15.90, "tags_meteo": ["Froid"], "is_featured": True, "Menu": ["À Partager"]},

    # Cocktails
    {"Plat": "Américano", "description_geo": "Vermouth italien, bitter campari, perrier, équilibre douceur amertume", "prix": 10.50, "tags_meteo": ["Chaud"], "is_featured": False, "Menu": ["Boissons"]},
    {"Plat": "Pina colada", "description_geo": "Crème de coco, ananas, rhum blanc, cocktail tropical", "prix": 9.50, "tags_meteo": ["Chaud"], "is_featured": False, "Menu": ["Boissons"]},
    {"Plat": "Sunset boulevard", "description_geo": "Orange, cranberry, pêche, mûre, vodka. Fruité et acidulé", "prix": 11.90, "tags_meteo": ["Chaud"], "is_featured": True, "Menu": ["Boissons"]},
    {"Plat": "Mojito", "description_geo": "Sucre, citron vert, rhum cubain, perrier, menthe, angostura", "prix": 10.50, "tags_meteo": ["Chaud"], "is_featured": False, "Menu": ["Boissons"]},
    {"Plat": "Paradis asiatique", "description_geo": "Sirop d'hibiscus, fleur d'hibiscus comestible, citron vert, prosecco", "prix": 11.50, "tags_meteo": ["Chaud"], "is_featured": True, "Menu": ["Boissons", "Asie"]},
    {"Plat": "Nana fizz", "description_geo": "Gin, perrier, sirop de sucre de canne, citron vert, framboise", "prix": 11.50, "tags_meteo": ["Chaud"], "is_featured": False, "Menu": ["Boissons"]},

    # Mocktails (Sans Alcool)
    {"Plat": "Prohibition (Mocktail)", "description_geo": "Jus d'orange, ananas, citron, sirop de framboise", "prix": 8.50, "tags_meteo": ["Chaud"], "is_featured": False, "Menu": ["Boissons"]},
    {"Plat": "Virgin mojito", "description_geo": "Sirop de canne, perrier, citron vert, menthe fraîche", "prix": 8.50, "tags_meteo": ["Chaud"], "is_featured": False, "Menu": ["Boissons"]},
    {"Plat": "L'exotique (Mocktail)", "description_geo": "Jus de banane, maracuja, pomme, vanille, citron vert", "prix": 9.50, "tags_meteo": ["Chaud"], "is_featured": False, "Menu": ["Boissons"]},
    {"Plat": "Virgin colada", "description_geo": "Jus d'ananas, crème de coco", "prix": 7.50, "tags_meteo": ["Chaud"], "is_featured": False, "Menu": ["Boissons"]},
    {"Plat": "Le délice (Mocktail)", "description_geo": "Jus de litchi, crème de framboise, citron, pomme", "prix": 11.50, "tags_meteo": ["Chaud"], "is_featured": False, "Menu": ["Boissons"]},

    # Plats de la mer
    {"Plat": "Grosses gambas grillées 3pc", "description_geo": "Gambas fraîches grillées au beurre et à l’ail, accompagnées de légumes grillés et riz parfumé", "prix": 29.90, "tags_meteo": ["Chaud"], "is_featured": True, "Menu": ["Côté Mer"]},
    {"Plat": "Moules à la crème beurre", "description_geo": "Moules sautées à la sauce beurre-crème, servies avec des frites", "prix": 16.90, "tags_meteo": ["Pluie"], "is_featured": False, "Menu": ["Côté Mer"]},
    {"Plat": "Pâtes aux fruits de mer", "description_geo": "Pâtes cuisinées avec crevettes, moules, calamars noix de saint-jacques, et sauce tomate fait maison", "prix": 19.90, "tags_meteo": ["Pluie"], "is_featured": False, "Menu": ["Côté Mer"]},
    {"Plat": "Riz sauté aux fruits de mer", "description_geo": "Riz parfumé associé aux crevettes, calamars et moules, noix de saint-jacques avec une touche de persil", "prix": 19.90, "tags_meteo": ["Chaud"], "is_featured": False, "Menu": ["Côté Mer", "Asie"]},
    {"Plat": "Assiette de fruits de mer", "description_geo": "Gambas, crevettes, sole, calamars, moules fraîches, noix de saint-jacques, délicatement harmonisés", "prix": 45.90, "tags_meteo": ["Chaud"], "is_featured": True, "Menu": ["Côté Mer"]},
    {"Plat": "Filet de bar au beurre", "description_geo": "Filet de bar délicatement nappée de sauce beurre accompagnée de riz parfumé et légumes grillés", "prix": 19.90, "tags_meteo": ["Chaud"], "is_featured": False, "Menu": ["Côté Mer"]},

    # Viandes / Plats de la terre
    {"Plat": "Poulet sauce teriyaki", "description_geo": "Blanc de poulet émincé, grillé sur brochettes et nappé de sauce teriyaki, servi avec riz parfumé et légumes grillés", "prix": 17.90, "tags_meteo": ["Chaud"], "is_featured": False, "Menu": ["Côté Terre", "Asie"]},
    {"Plat": "Faux filet de bœuf 250gr", "description_geo": "Faux filet de bœuf grillée, servie avec sauce maison et frites", "prix": 18.90, "tags_meteo": ["Froid"], "is_featured": False, "Menu": ["Côté Terre"]},
    {"Plat": "Tataki de bœuf 250gr", "description_geo": "Bœuf grillé tendre, tranché finement et mariné avec sauce fait maison, servi avec purée de pommes de terre et légumes grillés", "prix": 18.90, "tags_meteo": ["Chaud"], "is_featured": True, "Menu": ["Côté Terre", "Asie"]},
    {"Plat": "Filet de canard sauce fait maison", "description_geo": "Magret de canard grillé nappé sauce fait maison, servi avec des frites", "prix": 18.90, "tags_meteo": ["Froid"], "is_featured": False, "Menu": ["Côté Terre"]},
    {"Plat": "Filet de canard caramel balsamique", "description_geo": "Magret de canard grillé accompagné d'une sauce caramel balsamique onctueuse, servi avec purée de pomme de terre et légumes grillés", "prix": 18.90, "tags_meteo": ["Froid", "Pluie"], "is_featured": True, "Menu": ["Côté Terre"]},
    {"Plat": "Joue de bœuf braisée", "description_geo": "Joue de bœuf tendre braisée lentement au vin rouge, servie avec purée maison et carottes fondantes", "prix": 22.90, "tags_meteo": ["Froid", "Pluie"], "is_featured": True, "Menu": ["Côté Terre"]},

    # Menus et Formules
    {"Plat": "Formule Vietnamienne", "description_geo": "Entrée, Plat et Dessert au choix (Nems, Tiramisu, etc.)", "prix": 26.90, "tags_meteo": ["Chaud"], "is_featured": True, "Menu": ["Formules", "Asie"]},
    {"Plat": "Menu Enfant", "description_geo": "Plat au choix (Burger, Poulet, Pâtes) + 1 boule de glace", "prix": 12.90, "tags_meteo": [], "is_featured": False, "Menu": ["Formules"]},

    # Desserts
    {"Plat": "Tartelette tatin", "description_geo": "Tarte renversée aux pommes caramélisées sur beurre rehaussé de confitures, servie tiède.", "prix": 4.90, "tags_meteo": ["Froid", "Pluie"], "is_featured": False, "Menu": ["Douceurs"]},
    {"Plat": "Poire en trompe-l'œil", "description_geo": "Mousse poire onctueuse avec insert de compotée, façonnée comme une vraie poire.", "prix": 6.90, "tags_meteo": ["Chaud"], "is_featured": True, "Menu": ["Douceurs"]},
    {"Plat": "Tropézienne", "description_geo": "Brioche moelleuse garnie de crème mousseline, douce et délicate.", "prix": 4.50, "tags_meteo": ["Chaud"], "is_featured": False, "Menu": ["Douceurs"]},
    {"Plat": "Dôme rubis", "description_geo": "Mousse framboise avec coulis au cœur, sur biscuit Joconde, enrobée de chocolat noir et glaçage rouge rubis. Parfait pour conclure le repas.", "prix": 7.90, "tags_meteo": ["Chaud"], "is_featured": True, "Menu": ["Douceurs"]},
    {"Plat": "Tiramisu au café", "description_geo": "Tiramisu au café – Biscuits imbibés de café, crème mascarpone onctueuse, saupoudré de cacao, sans alcool.", "prix": 4.90, "tags_meteo": ["Froid"], "is_featured": False, "Menu": ["Douceurs"]},
    {"Plat": "Crème Brûlée au Café", "description_geo": "Crème onctueuse avec une fine couche de caramel croquant, parfumée au café.", "prix": 4.50, "tags_meteo": ["Froid"], "is_featured": False, "Menu": ["Douceurs"]},
    {"Plat": "Glaces (2 boules au choix)", "description_geo": "Glaces (2 boules au choix) surmontées de crème chantilly onctueuse (vanille, chocolat, rhum raisin, mangue, fraise, café, caramel).", "prix": 4.90, "tags_meteo": ["Chaud"], "is_featured": False, "Menu": ["Douceurs"]}
]

def populate_table():
    import time
    print(f"Insertion de {len(MENU_REEL)} plats bilingues avec catégories dans Airtable...")
    for item in MENU_REEL:
        plat_fr = item["Plat"]
        plat_en = ""
        desc_en = ""
        
        if plat_fr in TRANSLATIONS:
            plat_en, desc_en = TRANSLATIONS[plat_fr]
        
        payload = {
            "fields": {
                "Plat": plat_fr,
                "Plat_EN": plat_en,
                "description_geo": item["description_geo"],
                "description_geo_EN": desc_en,
                "tags_meteo": item["tags_meteo"],
                "prix": item["prix"],
                "is_featured": item["is_featured"],
                "Menu": item.get("Menu", []),
                "producteur_local": "Producteur du Sud-Ouest"
            }
        }
        res = requests.post(BASE_URL, headers=HEADERS, json=payload)
        if res.status_code == 200:
            print(f"✅ Ajouté: {plat_fr} ({', '.join(item.get('Menu', []))})")
        else:
            print(f"❌ Erreur sur {plat_fr}: {res.text}")
        time.sleep(0.25) # Rate limit respect (5 req/sec = 0.2s pause)

if __name__ == "__main__":
    clear_table()
    populate_table()
    print("Mise à jour de la carte bilingue terminée avec succès !")

