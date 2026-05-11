"""Script à lancer UNE FOIS en local pour obtenir le refresh_token Google.

Procédure :
    1. Renseigne CLIENT_ID et CLIENT_SECRET ci-dessous (ou via .env)
    2. python tools/get_business_refresh_token.py
    3. Une URL s'ouvre dans ton navigateur
    4. Connecte-toi avec lecherimoyarestaurant@gmail.com
    5. Clique "Autoriser"
    6. Google te redirige vers une page localhost qui peut afficher "site inaccessible"
       — c'est normal. Copie l'URL complète depuis la barre d'adresse
       (commence par http://localhost:8765/?code=...)
    7. Colle-la dans ce script qui affichera ton refresh_token
    8. Copie le refresh_token affiché et ajoute-le sur Vercel comme
       GOOGLE_BUSINESS_REFRESH_TOKEN.

Aucun serveur n'est démarré : le script lit juste l'URL que tu colles.
"""
import os
import sys
import webbrowser
from urllib.parse import urlencode, urlparse, parse_qs

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import requests

CLIENT_ID = os.getenv("GOOGLE_BUSINESS_CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("GOOGLE_BUSINESS_CLIENT_SECRET", "").strip()
REDIRECT_URI = "http://localhost:8765"
SCOPE = "https://www.googleapis.com/auth/business.manage"

if not CLIENT_ID or not CLIENT_SECRET:
    print("❌ GOOGLE_BUSINESS_CLIENT_ID et GOOGLE_BUSINESS_CLIENT_SECRET doivent être")
    print("   définis dans ton fichier .env local (pas sur Vercel — c'est juste pour")
    print("   ce script).")
    print()
    print("   Récupère-les sur https://console.cloud.google.com/apis/credentials")
    print("   → OAuth 2.0 Client IDs → Chérimoya Admin")
    sys.exit(1)

auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "response_type": "code",
    "scope": SCOPE,
    "access_type": "offline",
    "prompt": "consent",
})

print("=" * 70)
print("Étape 1 : ouverture de l'URL d'autorisation dans ton navigateur")
print("=" * 70)
print()
print(auth_url)
print()
webbrowser.open(auth_url)

print("Étape 2 : connecte-toi avec lecherimoyarestaurant@gmail.com")
print("Étape 3 : clique 'Autoriser'")
print("Étape 4 : Google te redirige vers localhost — la page affichera 'site inaccessible'")
print("          C'EST NORMAL. Copie l'URL complète depuis la barre d'adresse.")
print()
redirect_response = input("Colle l'URL complète ici : ").strip()

parsed = urlparse(redirect_response)
code = parse_qs(parsed.query).get("code", [None])[0]
if not code:
    print("❌ Pas de code trouvé dans l'URL collée.")
    sys.exit(1)

print()
print("Étape 5 : échange du code contre un refresh_token...")
resp = requests.post(
    "https://oauth2.googleapis.com/token",
    data={
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    },
    timeout=10,
)
if resp.status_code != 200:
    print(f"❌ Échange échoué : HTTP {resp.status_code}")
    print(resp.text)
    sys.exit(1)

data = resp.json()
refresh_token = data.get("refresh_token")
if not refresh_token:
    print("❌ Pas de refresh_token reçu. Réponse Google :")
    print(data)
    print()
    print("Solution : si tu as déjà autorisé l'app, révoque l'accès sur")
    print("https://myaccount.google.com/permissions puis relance ce script.")
    sys.exit(1)

print()
print("=" * 70)
print("✅ SUCCÈS — Voici ton refresh_token :")
print("=" * 70)
print()
print(refresh_token)
print()
print("=" * 70)
print("Étape 6 : sur Vercel → Settings → Environment Variables, ajoute :")
print()
print(f"  GOOGLE_BUSINESS_CLIENT_ID     = {CLIENT_ID}")
print(f"  GOOGLE_BUSINESS_CLIENT_SECRET = {CLIENT_SECRET[:6]}... (la valeur complète)")
print(f"  GOOGLE_BUSINESS_REFRESH_TOKEN = {refresh_token[:8]}... (la valeur complète)")
print()
print("Puis redéploie. Ce script n'a plus besoin d'être relancé.")
print("=" * 70)
