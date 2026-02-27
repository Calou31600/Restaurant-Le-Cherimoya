import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("AIRTABLE_API_KEY")
base_id = os.environ.get("AIRTABLE_BASE_ID")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

BASE_URL = f"https://api.airtable.com/v0/{base_id}/Dynamic_Menu"

TRANSLATIONS = {
    # Entrées
    "Salade de poulet croustillant": ("Crispy Chicken Salad", "Crispy chicken fillet with fresh green salad and homemade dressing"),
    "Salade de camembert rôti": ("Roasted Camembert Salad", "Honey-roasted Camembert cheese served with leafy greens, premium cured ham, and olives"),
    "Siu mai vapeur 5pc": ("Steamed Siu Mai (5 pcs)", "Delicate steamed dumplings filled with tender pork and fresh shrimp"),
    "Salade de nems": ("Spring Rolls Salad", "Crispy golden spring rolls served with fresh salad and homemade dipping sauce"),
    "Ha Kao aux crevettes 5pc": ("Steamed Ha Kao Shrimp Dumplings (5 pcs)", "Delicate translucent steamed dumplings filled with fresh shrimp"),
    
    # Apéritifs
    "Assiette d'apéritif - 4 nems": ("Appetizer Plate - 4 Spring Rolls", "4 crispy chicken spring rolls wrapped in fresh lettuce leaves"),
    "Plateau de fromages mixtes": ("Mixed Cheese Board", "A curated selection of seasonal cheeses to discover"),
    "Assiette de charcuterie et fromages": ("Charcuterie and Cheese Board", "Iberian ham, coppa, and a selection of premium cheeses to share"),
    
    # Cocktails
    "Américano": ("Americano", "Italian vermouth, bitter Campari, and sparkling water. A perfect balance of sweetness and bitterness"),
    "Pina colada": ("Pina Colada", "Coconut cream, pineapple juice, white rum. A tropical sunset in a glass"),
    "Sunset boulevard": ("Sunset Boulevard", "Orange, cranberry, peach, blackberry, and vodka. Fruity and tangy"),
    "Mojito": ("Mojito", "Cane sugar, fresh lime, Cuban rum, sparkling water, fresh mint, and Angostura bitters"),
    "Paradis asiatique": ("Asian Paradise", "Hibiscus syrup, edible hibiscus flower, lime, and Prosecco"),
    "Nana fizz": ("Nana Fizz", "Gin, sparkling water, cane sugar syrup, lime, and fresh raspberry"),
    
    # Mocktails
    "Prohibition (Mocktail)": ("Prohibition (Mocktail)", "Orange juice, pineapple, lemon, and raspberry syrup"),
    "Virgin mojito": ("Virgin Mojito", "Cane syrup, sparkling water, fresh lime, and mint leaves"),
    "L'exotique (Mocktail)": ("The Exotic (Mocktail)", "Banana juice, passion fruit, apple, vanilla, and lime"),
    "Virgin colada": ("Virgin Colada", "Pineapple juice and creamy coconut"),
    "Le délice (Mocktail)": ("The Delight (Mocktail)", "Lychee juice, raspberry cream, lemon, and apple"),
    
    # Mer
    "Grosses gambas grillées 3pc": ("Grilled Jumbo Prawns (3 pcs)", "Fresh prawns roasted with garlic and butter, served with grilled vegetables and rice"),
    "Moules à la crème beurre": ("Cream & Butter Mussels", "Mussels sautéed in a rich butter-cream sauce, served with French fries"),
    "Pâtes aux fruits de mer": ("Seafood Pasta", "Shrimp, mussels, calamari, and scallops in a rich tomato sauce"),
    "Riz sauté aux fruits de mer": ("Seafood Fried Rice", "Flavorful rice with shrimp, calamari, mussels, scallops, and fresh parsley"),
    "Assiette de fruits de mer": ("Seafood Platter", "Jumbo prawns, shrimp, sole fish, calamari, mussels, and scallops"),
    "Filet de bar au beurre": ("Sea Bass Fillet in Butter Sauce", "Sea bass fillet with a lemon butter sauce, served with rice and grilled vegetables"),
    "Crevettes sautées beurre ail": ("Garlic Butter Sautéed Shrimp", "Sautéed shrimp served with rice and grilled vegetables"),
    "Saumon sauce teriyaki": ("Teriyaki Salmon", "Grilled salmon fillet with homemade teriyaki sauce, served with rice and vegetables"),
    
    # Terre
    "Joue de bœuf confite au four": ("Oven-Braised Beef Cheek", "Beef cheek slow-cooked in wine, lovingly candied to melt-in-the-mouth perfection"),
    "Filet de poulet au cheddar": ("Cheddar Chicken Fillet", "Grilled chicken breast with melted cheddar, mushroom sauce, and fresh pasta"),
    "Côtes d'agneau grillées aux herbes": ("Herb-Grilled Lamb Chops", "Marinated rack of lamb with homemade sauce, creamy puree, and vegetables"),
    "Côte de bœuf 400g": ("Prime Rib 400g", "Generous prime rib served with signature sauce, crispy fries, and vegetables"),
    "Poulet sauce teriyaki": ("Teriyaki Chicken", "Grilled sliced chicken breast with teriyaki sauce and fragrant rice"),
    "Faux filet de bœuf 250gr": ("Sirloin Steak 250g", "Grilled sirloin steak served with homemade sauce and crispy French fries"),
    "Tataki de bœuf 250gr": ("Beef Tataki 250g", "Tender grilled beef, thinly sliced and marinated in our signature sauce"),
    "Filet de canard sauce fait maison": ("Duck Fillet with Signature Sauce", "Grilled duck breast served with the chef's special sauce and fries"),
    "Filet de canard caramel balsamique": ("Balsamic Caramel Duck Fillet", "Duck breast with a smooth balsamic caramel sauce, served with potato puree"),
    
    # Menus
    "Formule Vietnamienne": ("Vietnamese Set Menu", "Starter, Main Course, and Dessert of your choice (Spring Rolls, Tiramisu, etc.)"),
    "Menu Enfant": ("Kids Menu", "Main course of your choice (Burger, Chicken, Pasta) + 1 scoop of ice cream"),
    
    # Desserts
    "Tartelette tatin": ("Tarte Tatin", "Upside-down caramelized apple tart on a buttery crust, enhanced with fruit jam"),
    "Poire en trompe-l'œil": ("Trompe-l'œil Pear", "Smooth pear mousse with a compote center. A magnificent signature dessert"),
    "Tropézienne": ("Tropézienne Tart", "Soft brioche filled with delicate mousseline cream"),
    "Dôme rubis": ("Ruby Dome", "Raspberry mousse, pure coulis heart, Joconde biscuit, and ruby glaze"),
    "Tiramisu au café": ("Coffee Tiramisu", "Coffee-soaked biscuits with rich mascarpone cream (alcohol-free)"),
    "Crème Brûlée au Café": ("Coffee Crème Brûlée", "Smooth coffee cream topped with a crunchy caramelized layer"),
    "Glaces 2 boules": ("Ice Cream (2 scoops)", "Flavors of your choice, served with whipped cream")
}

def translate_records():
    url = BASE_URL
    records_updated = 0
    
    while True:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if "records" in data:
            for r in data["records"]:
                plat_fr = r["fields"].get("Plat")
                if plat_fr in TRANSLATIONS:
                    plat_en, desc_en = TRANSLATIONS[plat_fr]
                    
                    # Update record
                    patch_url = f"{BASE_URL}/{r['id']}"
                    payload = {
                        "fields": {
                            "Plat_EN": plat_en,
                            "description_geo_EN": desc_en
                        }
                    }
                    patch_res = requests.patch(patch_url, headers=headers, json=payload)
                    if patch_res.status_code == 200:
                        records_updated += 1
                        print(f"✅ Traduit: {plat_fr} -> {plat_en}")
                    else:
                        print(f"❌ Erreur sur {plat_fr}: {patch_res.text}")
                else:
                    print(f"⚠️ Traduction manquante pour: {plat_fr}")
                    
        if "offset" in data:
            url = f"{BASE_URL}?offset={data['offset']}"
        else:
            break
            
    print(f"\n🎉 Terminé ! {records_updated} plats traduits dans Airtable.")

if __name__ == "__main__":
    translate_records()
