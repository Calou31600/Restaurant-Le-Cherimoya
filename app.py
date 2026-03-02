import requests as http_requests
from flask import Flask, jsonify, send_from_directory, request, session, redirect, url_for, make_response
from flask_cors import CORS
import os
import sys
import cloudinary
import cloudinary.uploader
from authlib.integrations.flask_client import OAuth
from functools import wraps
from datetime import datetime
from werkzeug.middleware.proxy_fix import ProxyFix


# Ajouter le dossier tools au path pour importer les moteurs
sys.path.append(os.path.join(os.getcwd(), 'tools'))

from main_engine import MainEngine

app = Flask(__name__, static_folder='.')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "@ot!Jo?a#sDFnpXFSp#c!7X8&9FRR7J9LoemBQ$H")
CORS(app)

# ProxyFix : permet à Flask de détecter HTTPS derriere le proxy Vercel
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

REDIRECT_URI = "https://restaurant-le-cherimoya.vercel.app/authorize"

# BookingManager instancié INDÉPENDAMMENT — critique pour les réservations
try:
    from booking_manager import BookingManager as _BookingManager
    booking_manager = _BookingManager()
    print("[INIT] BookingManager OK")
except Exception as e:
    print(f"[INIT ERREUR] BookingManager : {e}")
    booking_manager = None

# MainEngine instancié de façon protégée — si weather/seo plante, le reste tient
try:
    engine = MainEngine()
    print("[INIT] MainEngine OK")
except Exception as e:
    print(f"[INIT ERREUR] MainEngine : {e}")
    engine = None


# Configuration Google OAuth - Récupération avec nettoyage (strip)
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    print("⚠️ ERREUR : GOOGLE_CLIENT_ID ou SECRET manquant dans les variables d'environnement !")

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

ADMIN_EMAIL = "lecherimoyarestaurant@gmail.com"

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session['user'].get('email') != ADMIN_EMAIL:
            # Sur les routes API, retourner du JSON (pas une redirection HTML)
            if request.path.startswith('/api/'):
                return jsonify({"status": "error", "error": "Non autorisé. Session expirée."}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# Configuration Cloudinary pour l'upload depuis le Dashboard
cloudinary_url = os.environ.get("CLOUDINARY_URL", "")
if cloudinary_url.startswith("cloudinary://"):
    creds = cloudinary_url.replace("cloudinary://", "")
    key_secret, cloud_name = creds.split("@")
    api_key, api_secret = key_secret.split(":")
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret
    )

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/login')
def login_page():
    return send_from_directory('.', 'login.html')

@app.route('/login/google')
def login_google():
    if not GOOGLE_CLIENT_ID:
        return "Erreur : Client ID Google manquant.", 500
    
    # URL de base pour l'authentification Google
    # On passe un 'state' bidon car nous n'allons pas le vérifier via la session
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        "response_type=code&"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        "scope=openid%20email%20profile&"
        "state=random_state_string"
    )
    return redirect(auth_url)


@app.route('/authorize')
def authorize():
    try:
        # 1. On récupère le code envoyé par Google
        code = request.args.get('code')
        if not code:
            return "Erreur : Aucun code reçu de Google.", 400

        # 2. On échange ce code contre un jeton d'accès via une requête POST directe
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'code': code,
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code'
        }
        
        token_resp = http_requests.post(token_url, data=data)
        if token_resp.status_code != 200:
            return f"Erreur Google Token : {token_resp.text}", 400
            
        access_token = token_resp.json().get('access_token')

        # 3. On récupère les infos de l'utilisateur avec ce jeton
        user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        user_resp = http_requests.get(user_info_url, headers={'Authorization': f'Bearer {access_token}'})
        user = user_resp.json()

        # 4. Vérification finale de l'admin
        if user and user.get('email') == ADMIN_EMAIL:
            session['user'] = dict(user)
            session.permanent = True
            return redirect(url_for('admin'))

        return f"Accès refusé : {user.get('email') if user else 'Inconnu'} n'est pas l'administrateur.", 403

    except Exception as e:
        print(f"ERREUR CRITIQUE AUTHORIZE : {e}")
        return f"Erreur d'authentification : {str(e)}", 500



@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/admin')
@admin_required
def admin():
    """Hub central de l'administration."""
    return send_from_directory('.', 'dashboard_hub.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Dashboard complet avec onglets."""
    return send_from_directory('.', 'dashboard.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/api/status')
def status():
    return jsonify({"status": "online", "restaurant": "Le Chérimoya"})

@app.route('/api/data')
def get_data():
    """Endpoint principal pour le frontend adaptatif."""
    try:
        if engine is None:
            return jsonify({"error": "Moteur non initialisé."}), 500
        data = engine.build_page_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reservations', methods=['POST'])
def make_reservation():
    try:
        data = request.json
        name = data.get('name')
        phone = data.get('phone')
        email = data.get('email')
        date_str = data.get('date')
        time_str = data.get('time')
        service = data.get('service')
        covers = data.get('covers')
        
        if not all([name, email, date_str, time_str, service, covers]):
            return jsonify({"status": "error", "message": "Veuillez remplir tous les champs obligatoires."}), 400

        bm = booking_manager
        if bm is None:
            from booking_manager import BookingManager as BM
            bm = BM()

        success, message = bm.submit_reservation(name, phone, email, date_str, time_str, service, covers)
        if success:
            return jsonify({"status": "success", "message": message})
        else:
            return jsonify({"status": "error", "message": message}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/reservations/action/<record_id>/<action>', methods=['GET'])
def handle_reservation_action(record_id, action):
    """Gère les clics depuis l'email de notification."""
    success, message = engine.booking.update_reservation_status(record_id, action)
    
    # On renvoie une petite page HTML propre pour l'utilisateur (le resto)
    display_status = "Confirmée" if action == "confirm" else "Annulée"
    bg_color = "#28a745" if action == "confirm" else "#dc3545"
    title_text = "Réservation Confirmée" if action == "confirm" else "Réservation Annulée"

    if not success:
        title_text = "Erreur"
        bg_color = "#f4a261" # Orange pour attention

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #1a1a1a; color: white;">
        <div style="text-align: center; padding: 40px; border-radius: 10px; background: #2a2a2a; border: 1px solid {bg_color}; max-width: 500px;">
            <h1 style="color: {bg_color};">{title_text} !</h1>
            <p style="font-size: 1.2rem;">{message}</p>
            {"<p style='color: #888;'>Le client recevra un e-mail automatique d'ici quelques secondes.</p>" if success else ""}
            <br>
            <a href="https://restaurant-le-cherimoya.vercel.app" style="color: white; text-decoration: none; border: 1px solid white; padding: 10px 20px; border-radius: 5px; display: inline-block; margin-top: 20px;">Retour au site</a>
        </div>
    </body>
    </html>
    """

# --- ROUTES ADMIN ---

@app.route('/api/admin/menu', methods=['GET'])
@admin_required
def admin_get_menu():
    """Liste tous les plats pour le dashboard."""
    try:
        raw_menu = engine.get_featured_menu()
        # On renvoie les ID Airtable pour permettre les PATCH ultérieurs
        menu_with_ids = [{"id": r["id"], "fields": r["fields"]} for r in raw_menu]
        return jsonify(menu_with_ids)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/menu/<record_id>', methods=['PATCH'])
@admin_required
def admin_update_item(record_id):
    """Met à jour un plat dans Airtable."""
    try:
        fields = request.json.get('fields', {})
        url = f"https://api.airtable.com/v0/{engine.base_id}/Dynamic_Menu/{record_id}"
        import requests
        res = requests.patch(url, headers=engine.headers, json={"fields": fields, "typecast": True})
        if res.status_code == 200:
            # Invalider le cache pour que le changement soit visible
            engine._cache.pop("menu", None)
            return jsonify({"status": "success", "data": res.json()})
        print(f"Erreur Airtable PATCH [{res.status_code}]: {res.text} pour les champs {fields}")
        return jsonify({"error": res.text}), res.status_code
    except Exception as e:
        print(f"Exception Route PATCH: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/menu/<record_id>', methods=['DELETE'])
@admin_required
def admin_delete_item(record_id):
    """Supprime un plat dans Airtable."""
    try:
        url = f"https://api.airtable.com/v0/{engine.base_id}/Dynamic_Menu/{record_id}"
        import requests
        res = requests.delete(url, headers=engine.headers)
        if res.status_code == 200:
            # Invalider le cache pour que le changement soit visible
            engine._cache.pop("menu", None)
            return jsonify({"status": "success", "data": res.json()})
        print(f"Erreur Airtable DELETE [{res.status_code}]: {res.text}")
        return jsonify({"error": res.text}), res.status_code
    except Exception as e:
        print(f"Exception Route DELETE: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/menu', methods=['POST'])
@admin_required
def admin_create_item():
    """Ajoute un nouveau plat dans Airtable."""
    try:
        fields = request.json.get('fields', {})
        url = f"https://api.airtable.com/v0/{engine.base_id}/Dynamic_Menu"
        import requests
        # Airtable requiert un objet 'records' de type array pour les POST
        res = requests.post(url, headers=engine.headers, json={"records": [{"fields": fields}], "typecast": True})
        if res.status_code == 200:
            # Invalider le cache pour que le changement soit visible
            engine._cache.pop("menu", None)
            return jsonify({"status": "success", "data": res.json()})
        print(f"Erreur Airtable POST [{res.status_code}]: {res.text} pour les champs {fields}")
        return jsonify({"error": res.text}), res.status_code
    except Exception as e:
        print(f"Exception Route POST: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/upload', methods=['POST'])
@admin_required
def admin_upload_image():
    """Upload une image vers Cloudinary."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files['file']
        upload_result = cloudinary.uploader.upload(file, folder="dashboard_uploads")
        return jsonify({"url": upload_result.get("secure_url")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- CRM CLIENTS ---

@app.route('/api/admin/clients', methods=['GET'])
@admin_required
def admin_get_clients():
    """Liste tous les clients."""
    try:
        clients = engine.get_clients()
        return jsonify(clients)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/clients/sync', methods=['POST'])
@admin_required
def admin_sync_clients():
    """Synchronise les clients à partir des réservations."""
    try:
        success, message = engine.sync_clients_from_reservations()
        if success:
            return jsonify({"status": "success", "message": message})
        return jsonify({"error": message}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/clients/send-review', methods=['POST'])
@admin_required
def admin_send_review():
    """Envoie une demande d'avis à un client."""
    try:
        data = request.json
        email = data.get('email')
        name = data.get('name')
        record_id = data.get('id') # ID Airtable du client

        if not email or not name:
            return jsonify({"error": "Email et nom requis."}), 400

        success, message = engine.booking.send_review_request(email, name)
        if success:
            # Mettre à jour la date d'envoi dans Airtable
            if record_id:
                today = datetime.now().strftime('%Y-%m-%d')
                url = f"https://api.airtable.com/v0/{engine.base_id}/Clients/{record_id}"
                http_requests.patch(url, headers=engine.headers, json={"fields": {"Dernier_Avis_Envoye": today}})
            
            return jsonify({"status": "success", "message": message})
        return jsonify({"error": message}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/clients/<record_id>', methods=['PATCH'])
@admin_required
def admin_update_client(record_id):
    """Met à jour les informations d'un client (ex: notes)."""
    try:
        fields = request.json.get('fields', {})
        url = f"https://api.airtable.com/v0/{engine.base_id}/Clients/{record_id}"
        res = http_requests.patch(url, headers=engine.headers, json={"fields": fields, "typecast": True})
        if res.status_code == 200:
            return jsonify({"status": "success", "data": res.json()})
        return jsonify({"error": res.text}), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/reservations', methods=['GET'])
@admin_required
def admin_get_reservations():
    """Liste toutes les réservations depuis Airtable (tri chronologique desc)."""
    try:
        bm = booking_manager
        if bm is None:
            from booking_manager import BookingManager as BM
            bm = BM()
        resas = bm.get_reservations()
        return jsonify(resas)
    except Exception as e:
        print(f"[GET RESERVATIONS] Erreur: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/reservations/action/<record_id>/<action>', methods=['POST'])
@admin_required
def admin_reservation_action(record_id, action):
    """Confirme ou annule une réservation depuis le dashboard."""
    try:
        print(f"[ADMIN ACTION] record_id={record_id} action={action}")
        if action not in ['confirm', 'cancel']:
            return jsonify({"status": "error", "error": "Action invalide."}), 400

        # Utiliser le BookingManager global indépendant
        bm = booking_manager
        if bm is None:
            # Dernier recours : instanciation locale
            from booking_manager import BookingManager as BM
            bm = BM()

        success, message = bm.update_reservation_status(record_id, action)
        print(f"[ADMIN ACTION] success={success} message={message}")

        if success:
            return jsonify({"status": "success", "message": message})
        return jsonify({"status": "error", "error": message}), 500
    except Exception as e:
        print(f"[ADMIN ACTION EXCEPTION] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/api/debug')
def api_debug():
    """Route de diagnostic — à supprimer en prod après débogage."""
    import os
    return jsonify({
        "engine_ok": engine is not None,
        "booking_ok": booking_manager is not None,
        "base_id": os.getenv('AIRTABLE_BASE_ID', 'MANQUANT'),
        "api_key_set": bool(os.getenv('AIRTABLE_API_KEY')),
    })


@app.route('/api/admin/stats/today', methods=['GET'])
@admin_required
def admin_get_today_stats():
    """Récupère les statistiques de réservation du jour (Midi et Soir)."""
    try:
        bm = booking_manager
        if bm is None:
            from booking_manager import BookingManager as BM
            bm = BM()
        stats = bm.get_today_stats()
        return jsonify(stats)
    except Exception as e:
        print(f"[STATS TODAY] Erreur: {e}")
        return jsonify({"error": str(e), "midi": 0, "soir": 0, "reservations_midi": [], "reservations_soir": []}), 500

@app.route('/admin/settings')
@admin_required
def admin_settings_page():
    """Page de configuration des paramètres du restaurant."""
    return send_from_directory('.', 'settings.html')

@app.route('/api/admin/settings', methods=['GET'])
@admin_required
def admin_get_settings():
    """Récupère les paramètres du restaurant."""
    try:
        from settings_manager import SettingsManager
        sm = SettingsManager()
        settings = sm.get_settings()
        return jsonify({"status": "success", "settings": settings})
    except Exception as e:
        print(f"[SETTINGS GET] Erreur: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/api/admin/settings', methods=['POST'])
@admin_required
def admin_save_settings():
    """Sauvegarde les paramètres du restaurant."""
    try:
        from settings_manager import SettingsManager
        sm = SettingsManager()
        settings = request.get_json()
        result = sm.save_settings(settings)
        return jsonify(result)
    except Exception as e:
        print(f"[SETTINGS SAVE] Erreur: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

if __name__ == '__main__':
    # On tourne sur le port 5000 par défaut
    print("Serveur Le Cherimoya demarre sur http://localhost:5000")
    print("Dashboard accessible sur http://localhost:5000/admin")
    app.run(debug=True, port=5000)
