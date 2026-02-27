import json
import os
from dotenv import load_dotenv

load_dotenv()

class SEOManager:
    """Génère les données structurées JSON-LD pour maximiser le AEO/SEO."""

    def __init__(self):
        self.restaurant_data = {
            "@context": "https://schema.org",
            "@type": "Restaurant",
            "name": "Le Chérimoya",
            "image": [
                "https://res.cloudinary.com/dgthsjtqn/image/upload/v1/restaurant_cherimoya/terroir/facade.jpg"
            ],
            "@id": "https://www.lecherimoya.fr",
            "url": "https://www.lecherimoya.fr",
            "telephone": "+335XXXXXXXX", # À compléter avec le vrai numéro
            "priceRange": "$$$",
            "menu": "https://www.lecherimoya.fr/carte",
            "servesCuisine": ["Fusion", "Gastronomique", "Terroir"],
            "acceptsReservations": "True",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "Villeneuve-de-Rivière",
                "addressLocality": "Villeneuve-de-Rivière",
                "postalCode": "31800",
                "addressRegion": "Haute-Garonne",
                "addressCountry": "FR"
            },
            "geo": {
                "@type": "GeoCoordinates",
                "latitude": 43.1215,
                "longitude": 0.6678
            },
            "openingHoursSpecification": [
                {
                    "@type": "OpeningHoursSpecification",
                    "dayOfWeek": ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                    "opens": "12:00",
                    "closes": "14:00"
                },
                {
                    "@type": "OpeningHoursSpecification",
                    "dayOfWeek": ["Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
                    "opens": "19:30",
                    "closes": "22:00"
                }
            ],
            "hasMenu": {
                "@type": "Menu",
                "name": "Carte de Saison du Comminges",
                "hasMenuItem": [] # Sera peuplé dynamiquement depuis Airtable
            }
        }

    def generate_json_ld(self, menu_items=None):
        """Génère le bloc script JSON-LD pour l'injection HTML."""
        data = self.restaurant_data.copy()
        if menu_items:
            for item in menu_items:
                data["hasMenu"]["hasMenuItem"].append({
                    "@type": "MenuItem",
                    "name": item.get("Plat"),
                    "description": item.get("description_geo"),
                    "offers": {
                        "@type": "Offer",
                        "price": item.get("prix"),
                        "priceCurrency": "EUR"
                    }
                })
        
        return json.dumps(data, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    seo = SEOManager()
    # Test à vide
    print(seo.generate_json_ld())
