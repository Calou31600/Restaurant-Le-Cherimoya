#!/usr/bin/env python3
"""
Script de test pour le système de paramètres.
"""

import sys
import os

# Ajouter le dossier tools au path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tools'))

from settings_manager import SettingsManager


def test_settings_manager():
    """Teste le SettingsManager."""

    print("="*60)
    print("   TEST DU SYSTÈME DE PARAMÈTRES")
    print("="*60)
    print()

    try:
        # Créer une instance du manager
        print("1️⃣  Création du SettingsManager...")
        sm = SettingsManager()
        print("   ✅ Manager créé avec succès")
        print()

        # Récupérer les paramètres
        print("2️⃣  Récupération des paramètres...")
        settings = sm.get_settings()
        print("   ✅ Paramètres récupérés:")
        print()
        for key, value in settings.items():
            if key != 'record_id':
                print(f"   • {key}: {value}")
        print()

        # Test de sauvegarde (optionnel - commenté pour ne pas modifier les données)
        # print("3️⃣  Test de sauvegarde...")
        # test_settings = {
        #     "totalSeats": 50,
        #     "maxReservationsPerDay": 100,
        #     "lunchStartTime": "12:00",
        #     "lunchEndTime": "14:00",
        #     "dinnerStartTime": "19:00",
        #     "dinnerEndTime": "22:00",
        #     "closedDays": [0],  # Dimanche
        #     "minAdvanceBookingHours": 2,
        #     "maxAdvanceBookingDays": 90
        # }
        # result = sm.save_settings(test_settings)
        # if result['status'] == 'success':
        #     print("   ✅ Sauvegarde réussie")
        # else:
        #     print(f"   ❌ Erreur: {result.get('error')}")
        # print()

        print("="*60)
        print("   ✅ TOUS LES TESTS SONT PASSÉS!")
        print("="*60)
        print()
        print("💡 Le système de paramètres est opérationnel.")
        print("   Vous pouvez accéder à l'interface via:")
        print("   http://localhost:5000/admin/settings")
        print()

        return True

    except Exception as e:
        print(f"   ❌ ERREUR: {e}")
        print()
        print("="*60)
        print("   ❌ LES TESTS ONT ÉCHOUÉ")
        print("="*60)
        print()
        print("💡 Assurez-vous que:")
        print("   1. La table Settings existe dans Airtable")
        print("      → Exécutez: python tools/create_settings_table.py")
        print()
        print("   2. Les variables d'environnement sont configurées")
        print("      → AIRTABLE_API_KEY")
        print("      → AIRTABLE_BASE_ID")
        print()
        return False


if __name__ == "__main__":
    success = test_settings_manager()
    exit(0 if success else 1)
