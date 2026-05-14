import os
import sys
import requests as http_requests
from flask import Flask, jsonify, send_from_directory, request, session, redirect, url_for, make_response
from flask_cors import CORS
from functools import wraps
from datetime import datetime
import json
from supabase import create_client, Client

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

# Supabase Client
sb_url = os.getenv("SUPABASE_URL")
sb_key = os.getenv("SUPABASE_KEY")
supabase_client: Client = create_client(sb_url, sb_key) if sb_url and sb_key else None

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
        lang = request.args.get('lang', 'fr').lower()
        data = engine.build_page_data(lang=lang)
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
            engine.clear_cache("menu")
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
            engine.clear_cache("menu")
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
            engine.clear_cache("menu")
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
            engine.clear_cache("wines")
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
            engine.clear_cache("wines")
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
            engine.clear_cache("wines")
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

@app.route('/api/admin/reservations/<record_id>', methods=['DELETE'])
@admin_required
def admin_delete_reservation(record_id):
    """Supprime une réservation sans envoyer d'email au client."""
    try:
        bm = booking_manager if booking_manager else BookingManager()
        success, message = bm.delete_reservation(record_id)
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

# --- ROUTES COMMANDES (tablette salle) ---

@app.route('/order')
def order_page():
    response = make_response(send_from_directory('.', 'order.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/kitchen')
def kitchen_page():
    response = make_response(send_from_directory('.', 'kitchen.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/facturation')
def facturation_page():
    response = make_response(send_from_directory('.', 'facturation.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/api/menu/public', methods=['GET'])
def get_public_menu():
    try:
        if not engine:
            return jsonify({"error": "Engine non chargé"}), 500
        records = engine.get_featured_menu()
        menu = []
        for r in records:
            f = r.get('fields', {})
            prix_raw = f.get('prix', '') or ''
            prix = 0.0
            try:
                prix = float(prix_raw.replace('€', '').replace(',', '.').strip())
            except Exception:
                pass
            categories = f.get('Menu', [])
            if isinstance(categories, str):
                categories = [categories]
            intol_raw = f.get('intolerances', '') or ''
            if isinstance(intol_raw, list):
                intolerances = [str(x).strip() for x in intol_raw if str(x).strip()]
            else:
                intolerances = [line.strip() for line in str(intol_raw).splitlines() if line.strip()]
            menu.append({
                'id': r['id'],
                'nom': f.get('Plat', ''),
                'description': f.get('description_geo', ''),
                'prix': prix,
                'prix_label': prix_raw,
                'photo': f.get('Photo', ''),
                'categories': categories,
                'intolerances': intolerances
            })
        return jsonify(menu)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    try:
        airtable_key = os.environ.get('AIRTABLE_API_KEY')
        base_id = os.environ.get('AIRTABLE_BASE_ID')
        at_headers = {"Authorization": f"Bearer {airtable_key}"}
        url = f"https://api.airtable.com/v0/{base_id}/Commandes"
        params = {"sort[0][field]": "Heure", "sort[0][direction]": "asc"}
        statut = request.args.get('statut')
        if statut:
            params["filterByFormula"] = f"{{Statut}}='{statut}'"
        res = http_requests.get(url, headers=at_headers, params=params)
        if res.status_code == 200:
            return jsonify(res.json().get('records', []))
        return jsonify({"error": res.text}), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/orders/table/<int:table_num>', methods=['GET'])
def get_table_orders(table_num):
    try:
        airtable_key = os.environ.get('AIRTABLE_API_KEY')
        base_id = os.environ.get('AIRTABLE_BASE_ID')
        at_headers = {"Authorization": f"Bearer {airtable_key}"}
        url = f"https://api.airtable.com/v0/{base_id}/Commandes"
        params = {
            "filterByFormula": f"AND({{Table_N}}={table_num},NOT(OR({{Statut}}='Servi',{{Statut}}='Payé',{{Statut}}='Annulé')))"
        }
        res = http_requests.get(url, headers=at_headers, params=params)
        if res.status_code == 200:
            return jsonify(res.json().get('records', []))
        return jsonify({"error": res.text}), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/orders', methods=['POST'])
def create_order():
    try:
        data = request.json
        table_num = data.get('table_num')
        items = data.get('items', [])
        total = data.get('total', 0)
        notes = data.get('notes', '')
        if not table_num or not items:
            return jsonify({"status": "error", "message": "Table et articles requis"}), 400
        now = datetime.now()
        service = "Midi" if now.hour < 17 else "Soir"
        heure_iso = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        ref = f"Table {table_num} - {now.strftime('%H:%M')}"
        airtable_key = os.environ.get('AIRTABLE_API_KEY')
        base_id = os.environ.get('AIRTABLE_BASE_ID')
        at_headers = {"Authorization": f"Bearer {airtable_key}", "Content-Type": "application/json"}
        fields = {
            "Ref": ref,
            "Table_N": int(table_num),
            "Items": json.dumps(items, ensure_ascii=False),
            "Total": float(total),
            "Statut": "En attente",
            "Heure": heure_iso,
            "Service": service,
            "Notes": notes
        }
        url = f"https://api.airtable.com/v0/{base_id}/Commandes"
        res = http_requests.post(url, headers=at_headers, json={"records": [{"fields": fields}]})
        if res.status_code == 200:
            return jsonify({"status": "success", "record": res.json()})
        return jsonify({"status": "error", "error": res.text}), res.status_code
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/api/orders/<record_id>', methods=['PATCH'])
def update_order_status(record_id):
    try:
        data = request.json
        statut = data.get('statut')
        if not statut:
            return jsonify({"status": "error", "message": "Statut requis"}), 400
        airtable_key = os.environ.get('AIRTABLE_API_KEY')
        base_id = os.environ.get('AIRTABLE_BASE_ID')
        at_headers = {"Authorization": f"Bearer {airtable_key}", "Content-Type": "application/json"}
        url = f"https://api.airtable.com/v0/{base_id}/Commandes/{record_id}"
        res = http_requests.patch(url, headers=at_headers, json={"fields": {"Statut": statut}})
        if res.status_code == 200:
            return jsonify({"status": "success"})
        return jsonify({"status": "error", "error": res.text}), res.status_code
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/api/billing/tables-ready', methods=['GET'])
def get_tables_ready_for_billing():
    """Retourne la liste des tables ayant au moins une commande Statut='Servi'."""
    try:
        airtable_key = os.environ.get('AIRTABLE_API_KEY')
        base_id = os.environ.get('AIRTABLE_BASE_ID')
        at_headers = {"Authorization": f"Bearer {airtable_key}"}
        url = f"https://api.airtable.com/v0/{base_id}/Commandes"
        params = {"filterByFormula": "{Statut}='Servi'", "fields[]": "Table_N"}
        res = http_requests.get(url, headers=at_headers, params=params)
        if res.status_code != 200:
            return jsonify({"error": res.text}), res.status_code
        tables = sorted({
            int(r['fields']['Table_N'])
            for r in res.json().get('records', [])
            if r.get('fields', {}).get('Table_N') is not None
        })
        return jsonify({"tables": tables})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/billing/table/<int:table_num>', methods=['GET'])
def get_billing_table(table_num):
    try:
        airtable_key = os.environ.get('AIRTABLE_API_KEY')
        base_id = os.environ.get('AIRTABLE_BASE_ID')
        at_headers = {"Authorization": f"Bearer {airtable_key}"}
        url = f"https://api.airtable.com/v0/{base_id}/Commandes"
        params = {
            "filterByFormula": f"AND({{Table_N}}={table_num},{{Statut}}='Servi')"
        }
        res = http_requests.get(url, headers=at_headers, params=params)
        if res.status_code != 200:
            return jsonify({"error": res.text}), res.status_code

        records = res.json().get('records', [])
        commande_ids = [r['id'] for r in records]

        aggregated = {}
        for record in records:
            fields = record.get('fields', {})
            items_raw = fields.get('Items', '[]')
            try:
                items = json.loads(items_raw)
            except Exception:
                items = []
            for item in items:
                item_id = item.get('id', item.get('nom', ''))
                if item_id in aggregated:
                    aggregated[item_id]['qty'] += item.get('qty', 1)
                else:
                    aggregated[item_id] = {
                        'nom': item.get('nom', ''),
                        'prix': float(item.get('prix', 0)),
                        'qty': item.get('qty', 1),
                        'categorie': item.get('categorie', item.get('categories', [''])[0] if isinstance(item.get('categories'), list) else '')
                    }

        return jsonify({
            "table": table_num,
            "commande_ids": commande_ids,
            "items": list(aggregated.values())
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/billing/close', methods=['POST'])
def close_billing():
    try:
        data = request.json
        commande_ids = data.get('commande_ids', [])
        if not commande_ids:
            return jsonify({"status": "error", "message": "Aucune commande à clôturer"}), 400

        airtable_key = os.environ.get('AIRTABLE_API_KEY')
        base_id = os.environ.get('AIRTABLE_BASE_ID')
        at_headers = {"Authorization": f"Bearer {airtable_key}", "Content-Type": "application/json"}

        errors = []
        for record_id in commande_ids:
            url = f"https://api.airtable.com/v0/{base_id}/Commandes/{record_id}"
            res = http_requests.patch(url, headers=at_headers, json={"fields": {"Statut": "Payé"}})
            if res.status_code != 200:
                errors.append(record_id)

        if errors:
            return jsonify({"status": "error", "message": f"Erreur sur {len(errors)} commande(s)"}), 500
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# --- ROUTES MENUS ÉVÉNEMENTS ---
# Stockés dans Airtable (table Special_Menus_Cherimoya). Le FS Vercel est read-only,
# donc tout doit passer par Airtable comme le reste de l'app.

SPECIAL_MENUS_TABLE = 'Special_Menus_Cherimoya'

def _sm_airtable_url(record_id=None):
    base_id = os.environ.get('AIRTABLE_BASE_ID')
    base_url = f"https://api.airtable.com/v0/{base_id}/{SPECIAL_MENUS_TABLE}"
    return f"{base_url}/{record_id}" if record_id else base_url

def _sm_airtable_headers():
    return {
        "Authorization": f"Bearer {os.environ.get('AIRTABLE_API_KEY')}",
        "Content-Type": "application/json",
    }

def _sm_record_to_menu(record):
    f = record.get('fields', {})
    def _split(v):
        if not v:
            return []
        return [line.strip() for line in str(v).splitlines() if line.strip()]
    return {
        'id':         record['id'],
        'name':       f.get('Name', ''),
        'theme':      f.get('Theme', 'personnalise'),
        'start_date': f.get('Start_Date', ''),
        'end_date':   f.get('End_Date', ''),
        'active':     bool(f.get('Active', False)),
        'price':      f.get('Price', ''),
        'subtitle':   f.get('Subtitle', ''),
        'entrees':    _split(f.get('Entrees', '')),
        'plats':      _split(f.get('Plats', '')),
        'desserts':   _split(f.get('Desserts', '')),
        'photo':      f.get('Photo', '')
    }

def _sm_payload_to_fields(data):
    def _join(items):
        if not items:
            return ''
        return '\n'.join(str(i).strip() for i in items if str(i).strip())
    mapping = {
        'name':       ('Name',       lambda v: v or ''),
        'theme':      ('Theme',      lambda v: v or 'personnalise'),
        'start_date': ('Start_Date', lambda v: v or ''),
        'end_date':   ('End_Date',   lambda v: v or ''),
        'active':     ('Active',     bool),
        'price':      ('Price',      lambda v: v or ''),
        'subtitle':   ('Subtitle',   lambda v: v or ''),
        'entrees':    ('Entrees',    _join),
        'plats':      ('Plats',      _join),
        'desserts':   ('Desserts',   _join),
        'photo':      ('Photo',      lambda v: v or ''),
    }
    fields = {}
    for key, (col, cast) in mapping.items():
        if key in data:
            fields[col] = cast(data.get(key))
    return fields

def load_special_menus():
    """Récupère les menus spéciaux depuis Supabase."""
    if not supabase_client: return []
    try:
        res = supabase_client.table("special_menus").select("*").execute()
        return [{
            "id": r["id"],
            "name": r["name"],
            "theme": r["theme"],
            "start_date": r["start_date"],
            "end_date": r["end_date"],
            "active": r["active"],
            "price": r["price"],
            "subtitle": r["subtitle"],
            "entrees": (r["entrees"] or "").splitlines(),
            "plats": (r["plats"] or "").splitlines(),
            "desserts": (r["desserts"] or "").splitlines(),
            "photo": r["photo"]
        } for r in res.data]
    except Exception as e:
        print(f"[Supabase] Erreur load_special_menus: {e}")
        return []

@app.route('/api/special-menus/active', methods=['GET'])
def get_active_special_menu():
    today = datetime.now().strftime('%Y-%m-%d')
    for m in load_special_menus():
        if not m.get('active', True):
            continue
        start, end = m.get('start_date', ''), m.get('end_date', '')
        if start and end and start <= today <= end:
            return jsonify(m)
    return jsonify(None)

@app.route('/api/admin/special-menus', methods=['GET'])
@admin_required
def admin_get_special_menus():
    return jsonify(load_special_menus())

@app.route('/api/admin/special-menus', methods=['POST'])
@admin_required
def admin_create_special_menu():
    data = request.json or {}
    fields = {
        "name": data.get("name"),
        "theme": data.get("theme", "personnalise"),
        "start_date": data.get("start_date"),
        "end_date": data.get("end_date"),
        "active": data.get("active", True),
        "price": data.get("price"),
        "subtitle": data.get("subtitle"),
        "entrees": "\n".join(data.get("entrees", [])),
        "plats": "\n".join(data.get("plats", [])),
        "desserts": "\n".join(data.get("desserts", [])),
        "photo": data.get("photo")
    }
    try:
        res = supabase_client.table("special_menus").insert(fields).execute()
        return jsonify({'status': 'success', 'menu': res.data[0]})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/admin/special-menus/<menu_id>', methods=['PATCH'])
@admin_required
def admin_update_special_menu(menu_id):
    data = request.json or {}
    fields = {}
    mapping = ["name", "theme", "start_date", "end_date", "active", "price", "subtitle", "photo"]
    for k in mapping:
        if k in data: fields[k] = data[k]
    
    if "entrees" in data: fields["entrees"] = "\n".join(data["entrees"])
    if "plats" in data: fields["plats"] = "\n".join(data["plats"])
    if "desserts" in data: fields["desserts"] = "\n".join(data["desserts"])

    try:
        supabase_client.table("special_menus").update(fields).eq("id", menu_id).execute()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/api/admin/special-menus/<menu_id>', methods=['DELETE'])
@admin_required
def admin_delete_special_menu(menu_id):
    try:
        supabase_client.table("special_menus").delete().eq("id", menu_id).execute()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
