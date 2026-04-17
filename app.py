import os
import sys
import requests as http_requests
from flask import Flask, jsonify, send_from_directory, request, session, redirect, url_for, make_response
from flask_cors import CORS
from functools import wraps
from datetime import datetime

# Configuration Cloudinary et Authlib
import cloudinary
import cloudinary.uploader
from authlib.integrations.flask_client import OAuth

# Ajouter le dossier tools au path pour importer les moteurs
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
tools_path = os.path.join(BASE_PATH, 'tools')
if tools_path not in sys.path:
    sys.path.append(tools_path)

# Import sécurisé du MainEngine
try:
    from main_engine import MainEngine
except ImportError as e:
    print(f"⚠️ ERREUR IMPORT MainEngine : {e}")
    MainEngine = None

app = Flask(__name__, static_folder='.')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "@ot!Jo?a#sDFnpXFSp#c!7X8&9FRR7J9LoemBQ$H")

@app.route('/api/ping')
def ping():
    return jsonify({
        "status": "pong", 
        "timestamp": datetime.now().isoformat(),
        "engine_loaded": MainEngine is not None,
        "python_version": sys.version
    })

CORS(app)

# ProxyFix sécurisé pour la détection HTTPS sur Vercel
try:
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
except Exception as e:
    print(f"⚠️ ProxyFix Error: {e}")

REDIRECT_URI = "https://restaurant-le-cherimoya.vercel.app/authorize"

# Initialisation des moteurs (BookingManager et MainEngine)
booking_manager = None
try:
    from booking_manager import BookingManager
    booking_manager = BookingManager()
    print("[INIT] BookingManager OK")
except Exception as e:
    print(f"⚠️ BookingManager Init Error: {e}")

engine = None
if MainEngine:
    try:
        engine = MainEngine()
        print("[INIT] MainEngine OK")
    except Exception as e:
        print(f"⚠️ MainEngine Init Error: {e}")

# Configuration Google OAuth
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()

oauth = OAuth(app)
google = None
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    try:
        google = oauth.register(
            name='google',
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile'}
        )
    except Exception as e:
        print(f"⚠️ Google OAuth Error: {e}")

ADMIN_EMAIL = "lecherimoyarestaurant@gmail.com"

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or session['user'].get('email') != ADMIN_EMAIL:
            if request.path.startswith('/api/'):
                return jsonify({"status": "error", "error": "Non autorisé. Session expirée."}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# Configuration Cloudinary
cloudinary_url = os.environ.get("CLOUDINARY_URL", "")
if cloudinary_url.startswith("cloudinary://"):
    try:
        creds = cloudinary_url.replace("cloudinary://", "")
        key_secret, cloud_name = creds.split("@")
        api_key, api_secret = key_secret.split(":")
        cloudinary.config(cloud_name=cloud_name, api_key=api_key, api_secret=api_secret)
    except Exception as e:
        print(f"⚠️ Cloudinary Config Error: {e}")

# --- ROUTES SITE PUBLIC ---

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
        code = request.args.get('code')
        if not code:
            return "Erreur : Aucun code reçu de Google.", 400

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
        user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        user_resp = http_requests.get(user_info_url, headers={'Authorization': f'Bearer {access_token}'})
        user = user_resp.json()

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

# --- ROUTES ADMIN ---

@app.route('/admin')
@admin_required
def admin():
    response = make_response(send_from_directory('.', 'dashboard_hub.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    response = make_response(send_from_directory('.', 'dashboard.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/admin/settings')
@admin_required
def admin_settings_page():
    return send_from_directory('.', 'settings.html')

@app.route('/api/status')
def status():
    return jsonify({"status": "online", "restaurant": "Le Chérimoya"})

@app.route('/api/data')
def get_data():
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

        bm = booking_manager if booking_manager else BookingManager()
        success, message = bm.submit_reservation(name, phone, email, date_str, time_str, service, covers)
        
        if success:
            return jsonify({"status": "success", "message": message})
        return jsonify({"status": "error", "message": message}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/admin/reservations/manual', methods=['POST'])
@admin_required
def admin_manual_reservation():
    try:
        data = request.json
        name = data.get('name')
        phone = data.get('phone', '')
        email = data.get('email', '')
        date = data.get('date')
        time = data.get('time')
        service = data.get('service')
        covers = data.get('covers')

        if not all([name, date, time, service, covers]):
            return jsonify({"status": "error", "message": "Champs obligatoires manquants."}), 400

        bm = booking_manager if booking_manager else BookingManager()
        success, message = bm.create_manual_reservation(name, phone, email, date, time, service, covers)
        
        if success:
            return jsonify({"status": "success", "message": message})
        return jsonify({"status": "error", "message": message}), 500
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/api/reservations/action/<record_id>/<action>', methods=['GET'])
def handle_reservation_action(record_id, action):
    bm = booking_manager if booking_manager else BookingManager()
    success, message = bm.update_reservation_status(record_id, action)
    
    bg_color = "#28a745" if action == "confirm" else "#dc3545"
    title_text = "Réservation Confirmée" if action == "confirm" else "Réservation Annulée"

    if not success:
        title_text = "Erreur"
        bg_color = "#f4a261"

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #1a1a1a; color: white;">
        <div style="text-align: center; padding: 40px; border-radius: 10px; background: #2a2a2a; border: 1px solid {bg_color}; max-width: 500px;">
            <h1 style="color: {bg_color};">{title_text} !</h1>
            <p style="font-size: 1.2rem;">{message}</p>
            <br>
            <a href="https://restaurant-le-cherimoya.vercel.app" style="color: white; text-decoration: none; border: 1px solid white; padding: 10px 20px; border-radius: 5px; display: inline-block; margin-top: 20px;">Retour au site</a>
        </div>
    </body>
    </html>
    """

@app.route('/api/admin/menu', methods=['GET'])
@admin_required
def admin_get_menu():
    try:
        if not engine: return jsonify({"error": "Engine non chargé"}), 500
        raw_menu = engine.get_featured_menu()
        menu_with_ids = [{"id": r["id"], "fields": r["fields"]} for r in raw_menu]
        return jsonify(menu_with_ids)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/menu/<record_id>', methods=['GET'])
@admin_required
def admin_get_item(record_id):
    try:
        url = f"https://api.airtable.com/v0/{engine.base_id}/Dynamic_Menu/{record_id}"
        res = http_requests.get(url, headers=engine.headers)
        if res.status_code == 200:
            return jsonify(res.json())
        return jsonify({"error": res.text}), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/menu/<record_id>', methods=['PATCH'])
@admin_required
def admin_update_item(record_id):
    try:
        fields = request.json.get('fields', {})
        # is_featured est un champ multilineText dans Airtable : False doit être ""
        # sinon Airtable stocke la chaîne "false" qui est truthy en JS
        if 'is_featured' in fields:
            fields['is_featured'] = "true" if fields['is_featured'] else ""
        url = f"https://api.airtable.com/v0/{engine.base_id}/Dynamic_Menu/{record_id}"
        res = http_requests.patch(url, headers=engine.headers, json={"fields": fields, "typecast": True})
        if res.status_code == 200:
            engine._cache.pop("menu", None)
            return jsonify({"status": "success", "data": res.json()})
        return jsonify({"error": res.text}), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/menu/<record_id>', methods=['DELETE'])
@admin_required
def admin_delete_item(record_id):
    try:
        url = f"https://api.airtable.com/v0/{engine.base_id}/Dynamic_Menu/{record_id}"
        res = http_requests.delete(url, headers=engine.headers)
        if res.status_code == 200:
            engine._cache.pop("menu", None)
            return jsonify({"status": "success", "data": res.json()})
        return jsonify({"error": res.text}), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/menu', methods=['POST'])
@admin_required
def admin_create_item():
    try:
        fields = request.json.get('fields', {})
        if 'is_featured' in fields:
            fields['is_featured'] = "true" if fields['is_featured'] else ""
        url = f"https://api.airtable.com/v0/{engine.base_id}/Dynamic_Menu"
        res = http_requests.post(url, headers=engine.headers, json={"records": [{"fields": fields}], "typecast": True})
        if res.status_code == 200:
            engine._cache.pop("menu", None)
            return jsonify({"status": "success", "data": res.json()})
        return jsonify({"error": res.text}), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/wines', methods=['GET'])
@admin_required
def admin_get_wines():
    try:
        if not engine: return jsonify({"error": "Engine non chargé"}), 500
        raw = engine.get_wine_list()
        return jsonify([{"id": r["id"], "fields": r["fields"]} for r in raw])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/wines/<record_id>', methods=['GET'])
@admin_required
def admin_get_wine(record_id):
    try:
        url = f"https://api.airtable.com/v0/{engine.base_id}/Carte_Vins/{record_id}"
        res = http_requests.get(url, headers=engine.headers)
        if res.status_code == 200:
            return jsonify(res.json())
        return jsonify({"error": res.text}), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/wines/<record_id>', methods=['PATCH'])
@admin_required
def admin_update_wine(record_id):
    try:
        fields = request.json.get('fields', {})
        url = f"https://api.airtable.com/v0/{engine.base_id}/Carte_Vins/{record_id}"
        res = http_requests.patch(url, headers=engine.headers, json={"fields": fields, "typecast": True})
        if res.status_code == 200:
            engine._cache.pop("wines", None)
            return jsonify({"status": "success", "data": res.json()})
        return jsonify({"error": res.text}), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/wines/<record_id>', methods=['DELETE'])
@admin_required
def admin_delete_wine(record_id):
    try:
        url = f"https://api.airtable.com/v0/{engine.base_id}/Carte_Vins/{record_id}"
        res = http_requests.delete(url, headers=engine.headers)
        if res.status_code == 200:
            engine._cache.pop("wines", None)
            return jsonify({"status": "success", "data": res.json()})
        return jsonify({"error": res.text}), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/wines', methods=['POST'])
@admin_required
def admin_create_wine():
    try:
        fields = request.json.get('fields', {})
        url = f"https://api.airtable.com/v0/{engine.base_id}/Carte_Vins"
        res = http_requests.post(url, headers=engine.headers, json={"records": [{"fields": fields}], "typecast": True})
        if res.status_code == 200:
            engine._cache.pop("wines", None)
            return jsonify({"status": "success", "data": res.json()})
        return jsonify({"error": res.text}), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/upload', methods=['POST'])
@admin_required
def admin_upload_image():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files['file']
        upload_result = cloudinary.uploader.upload(file, folder="dashboard_uploads")
        return jsonify({"url": upload_result.get("secure_url")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/clients', methods=['GET'])
@admin_required
def admin_get_clients():
    try:
        return jsonify(engine.get_clients())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/clients/sync', methods=['POST'])
@admin_required
def admin_sync_clients():
    try:
        success, message = engine.sync_clients_from_reservations()
        return jsonify({"status": "success" if success else "error", "message": message})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/reservations', methods=['GET'])
@admin_required
def admin_get_reservations():
    try:
        bm = booking_manager if booking_manager else BookingManager()
        return jsonify(bm.get_reservations())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/reservations/action/<record_id>/<action>', methods=['POST'])
@admin_required
def admin_reservation_action(record_id, action):
    try:
        bm = booking_manager if booking_manager else BookingManager()
        success, message = bm.update_reservation_status(record_id, action)
        return jsonify({"status": "success" if success else "error", "message": message})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/api/admin/stats/today', methods=['GET'])
@admin_required
def admin_get_today_stats():
    try:
        bm = booking_manager if booking_manager else BookingManager()
        return jsonify(bm.get_today_stats())
    except Exception as e:
        return jsonify({"error": str(e), "midi": 0, "soir": 0}), 500

@app.route('/api/admin/settings', methods=['GET'])
@admin_required
def admin_get_settings():
    try:
        from settings_manager import SettingsManager
        sm = SettingsManager()
        return jsonify({"status": "success", "settings": sm.get_settings()})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/api/admin/settings', methods=['POST'])
@admin_required
def admin_save_settings():
    try:
        from settings_manager import SettingsManager
        sm = SettingsManager()
        return jsonify(sm.save_settings(request.get_json()))
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
