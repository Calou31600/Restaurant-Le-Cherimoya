#!/usr/bin/env python3
"""
Script pour créer la table Settings dans Airtable.
Cette table stocke les paramètres globaux du restaurant.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def create_settings_table():
    """Crée la table Settings avec les champs nécessaires dans Airtable."""

    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')

    if not api_key or not base_id:
        print("ERROR: AIRTABLE_API_KEY or AIRTABLE_BASE_ID missing in .env")
        return False

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # URL pour créer une table
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"

    # Définition de la structure de la table Settings
    table_schema = {
        "name": "Settings_Cherimoya",
        "description": "Paramètres globaux du restaurant (capacité, horaires, etc.)",
        "fields": [
            {
                "name": "totalSeats",
                "type": "number",
                "description": "Nombre total de places dans le restaurant",
                "options": {"precision": 0}
            },
            {
                "name": "maxReservationsPerDay",
                "type": "number",
                "description": "Nombre maximum de réservations par jour",
                "options": {"precision": 0}
            },
            {
                "name": "lunchStartTime",
                "type": "singleLineText",
                "description": "Heure de début du service midi (format HH:MM)"
            },
            {
                "name": "lunchEndTime",
                "type": "singleLineText",
                "description": "Heure de fin du service midi (format HH:MM)"
            },
            {
                "name": "dinnerStartTime",
                "type": "singleLineText",
                "description": "Heure de début du service soir (format HH:MM)"
            },
            {
                "name": "dinnerEndTime",
                "type": "singleLineText",
                "description": "Heure de fin du service soir (format HH:MM)"
            },
            {
                "name": "closedDays",
                "type": "multipleSelects",
                "description": "Jours de fermeture (0=Dimanche, 1=Lundi, etc.)",
                "options": {
                    "choices": [
                        {"name": "0"},
                        {"name": "1"},
                        {"name": "2"},
                        {"name": "3"},
                        {"name": "4"},
                        {"name": "5"},
                        {"name": "6"}
                    ]
                }
            },
            {
                "name": "minAdvanceBookingHours",
                "type": "number",
                "description": "Délai minimum de réservation en heures",
                "options": {"precision": 0}
            },
            {
                "name": "maxAdvanceBookingDays",
                "type": "number",
                "description": "Délai maximum de réservation en jours",
                "options": {"precision": 0}
            }
        ]
    }

    print("Creating Settings table in Airtable...")
    print(f"   Base ID: {base_id}")

    try:
        response = requests.post(url, json=table_schema, headers=headers, timeout=10)

        if response.status_code == 200:
            print("SUCCESS: Settings table created!")
            result = response.json()
            print(f"   Table ID: {result.get('id')}")

            # Créer un enregistrement par défaut
            create_default_settings(api_key, base_id)
            return True
        else:
            print(f"ERROR: table creation failed: {response.status_code}")
            print(f"   Réponse: {response.text}")

            # Si la table existe déjà, c'est OK
            if "TABLE_ALREADY_EXISTS" in response.text or response.status_code == 422:
                print("INFO: Settings table already exists")
                return True
            return False

    except Exception as e:
        print(f"ERROR: request failed: {e}")
        return False


def create_default_settings(api_key, base_id):
    """Crée un enregistrement par défaut dans la table Settings."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    url = f"https://api.airtable.com/v0/{base_id}/Settings_Cherimoya"

    default_data = {
        "fields": {
            "totalSeats": 50,
            "maxReservationsPerDay": 100,
            "lunchStartTime": "12:00",
            "lunchEndTime": "14:00",
            "dinnerStartTime": "19:00",
            "dinnerEndTime": "22:00",
            "minAdvanceBookingHours": 2,
            "maxAdvanceBookingDays": 90
        }
    }

    print("\n📝 Création de l'enregistrement par défaut...")

    try:
        response = requests.post(url, json=default_data, headers=headers, timeout=10)

        if response.status_code == 200:
            print("SUCCESS: Default settings created!")
            result = response.json()
            print(f"   Record ID: {result.get('id')}")
        else:
            print(f"WARNING: could not create default settings: {response.status_code}")
            print(f"   (Vous pouvez le créer manuellement depuis l'interface)")

    except Exception as e:
        print(f"WARNING: error creating record: {e}")


if __name__ == "__main__":
    print("="*60)
    print("   CRÉATION DE LA TABLE SETTINGS DANS AIRTABLE")
    print("="*60)
    print()

    success = create_settings_table()

    print()
    if success:
        print("✅ Configuration terminée avec succès!")
        print()
        print("💡 Vous pouvez maintenant accéder aux paramètres via:")
        print("   http://localhost:5000/admin/settings")
    else:
        print("ERROR: configuration failed.")
        print()
        print("💡 Assurez-vous que:")
        print("   - AIRTABLE_API_KEY et AIRTABLE_BASE_ID sont définis dans .env")
        print("   - Votre clé API a les permissions nécessaires")

    print()
    print("="*60)
