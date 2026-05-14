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
# Côté serveur, on préfère la clé service_role si disponible (contourne RLS).
# La clé publishable reste un fallback acceptable tant que RLS n'est pas activée.
sb_url = os.getenv("SUPABASE_URL")
sb_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
supabase_client: Client = None
if sb_url and sb_key:
    try:
        supabase_client = create_client(sb_url, sb_key)
    except Exception as e:
        print(f"⚠️ Erreur initialisation Supabase: {e}")

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

def _menu_row_to_fields(r):
    """Format Supabase row → payload attendu par dashboard.html (clés Airtable-like)."""
    return {
        "id": r["id"],
        "fields": {
            "Plat":                r.get("plat"),
            "Plat_EN":             r.get("plat_en"),
            "description_geo":     r.get("description_geo"),
            "description_geo_EN":  r.get("description_geo_en"),
            "prix":                f"€{r['prix']:.2f}" if r.get("prix") else "",
            "tags_meteo":          r.get("tags_meteo") or [],
            "Menu":                r.get("menu") or [],
            "intolerances":        r.get("intolerances") or [],
            "producteur_local":    r.get("producteur_local"),
            "is_featured":         r.get("is_featured"),
            "Photo":               [{"url": r["photo"]}] if r.get("photo") else [],
        },
    }


def _menu_payload_from_fields(fields):
    """Payload admin (clés Airtable-like) → colonnes Supabase. Ne mappe que les
    clés présentes pour permettre des PATCH partiels."""
    out = {}
    if "Plat" in fields:               out["plat"]                = fields["Plat"]
    if "Plat_EN" in fields:            out["plat_en"]             = fields["Plat_EN"]
    if "description_geo" in fields:    out["description_geo"]     = fields["description_geo"]
    if "description_geo_EN" in fields: out["description_geo_en"]  = fields["description_geo_EN"]
    if "prix" in fields:
        try:
            out["prix"] = float(str(fields["prix"]).replace("€", "").replace(",", ".").strip())
        except (TypeError, ValueError):
            pass
    if "tags_meteo" in fields:         out["tags_meteo"]          = fields["tags_meteo"] or []
    if "Menu" in fields:               out["menu"]                = fields["Menu"] or []
    if "intolerances" in fields:       out["intolerances"]        = fields["intolerances"] or []
    if "producteur_local" in fields:   out["producteur_local"]    = fields["producteur_local"]
    if "is_featured" in fields:        out["is_featured"]         = bool(fields["is_featured"])
    if "Photo" in fields:
        photo = fields["Photo"]
        if isinstance(photo, list) and photo:
            out["photo"] = photo[0].get("url")
        elif isinstance(photo, str):
            out["photo"] = photo
        else:
            out["photo"] = None
    return out


@app.route('/api/admin/menu', methods=['GET'])
@admin_required
def admin_get_menu():
    try:
        if not supabase_client: return jsonify({"error": "Supabase non connecté"}), 500
        res = supabase_client.table("menu").select("*").execute()
        return jsonify([_menu_row_to_fields(r) for r in res.data])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/menu/<record_id>', methods=['GET'])
@admin_required
def admin_get_item(record_id):
    try:
        res = supabase_client.table("menu").select("*").eq("id", record_id).execute()
        if res.data:
            return jsonify(_menu_row_to_fields(res.data[0]))
        return jsonify({"error": "Not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/menu/<record_id>', methods=['PATCH'])
@admin_required
def admin_update_item(record_id):
    try:
        update_data = _menu_payload_from_fields(request.json.get('fields', {}))
        supabase_client.table("menu").update(update_data).eq("id", record_id).execute()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/menu/<record_id>', methods=['DELETE'])
@admin_required
def admin_delete_item(record_id):
    try:
        supabase_client.table("menu").delete().eq("id", record_id).execute()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/menu', methods=['POST'])
@admin_required
def admin_create_item():
    try:
        insert_data = _menu_payload_from_fields(request.json.get('fields', {}))
        insert_data.setdefault("prix", 0.0)
        insert_data.setdefault("is_featured", False)
        insert_data.setdefault("tags_meteo", [])
        insert_data.setdefault("menu", [])
        insert_data.setdefault("intolerances", [])
        res = supabase_client.table("menu").insert(insert_data).execute()
        return jsonify({"status": "success", "data": res.data[0]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def _wine_row_to_fields(r):
    return {
        "id": r["id"],
        "fields": {
            "Nom":             r.get("nom"),
            "Nom_EN":          r.get("nom_en"),
            "Appellation":     r.get("appellation"),
            "Millesime":       r.get("millesime"),
            "Prix_Verre":      r.get("prix_verre"),
            "Prix_Bouteille":  r.get("prix_bouteille"),
            "Type":            r.get("type"),
            "Description":     r.get("description"),
            "Description_EN":  r.get("description_en"),
            "Photo":           [{"url": r["photo"]}] if r.get("photo") else [],
        },
    }


def _wine_payload_from_fields(fields):
    out = {}
    mapping = {
        "Nom":            "nom",
        "Nom_EN":         "nom_en",
        "Appellation":    "appellation",
        "Millesime":      "millesime",
        "Prix_Verre":     "prix_verre",
        "Prix_Bouteille": "prix_bouteille",
        "Type":           "type",
        "Description":    "description",
        "Description_EN": "description_en",
    }
    for k, col in mapping.items():
        if k in fields:
            out[col] = fields[k]
    if "Photo" in fields:
        photo = fields["Photo"]
        if isinstance(photo, list) and photo:
            out["photo"] = photo[0].get("url")
        elif isinstance(photo, str):
            out["photo"] = photo
        else:
            out["photo"] = None
    return out


@app.route('/api/admin/wines', methods=['GET'])
@admin_required
def admin_get_wines():
    try:
        if not supabase_client: return jsonify({"error": "Supabase non connecté"}), 500
        res = supabase_client.table("wines").select("*").execute()
        return jsonify([_wine_row_to_fields(r) for r in res.data])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/wines/<record_id>', methods=['GET'])
@admin_required
def admin_get_wine(record_id):
    try:
        res = supabase_client.table("wines").select("*").eq("id", record_id).execute()
        if res.data:
            return jsonify(_wine_row_to_fields(res.data[0]))
        return jsonify({"error": "Not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/wines/<record_id>', methods=['PATCH'])
@admin_required
def admin_update_wine(record_id):
    try:
        update_data = _wine_payload_from_fields(request.json.get('fields', {}))
        supabase_client.table("wines").update(update_data).eq("id", record_id).execute()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/wines/<record_id>', methods=['DELETE'])
@admin_required
def admin_delete_wine(record_id):
    try:
        supabase_client.table("wines").delete().eq("id", record_id).execute()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/wines', methods=['POST'])
@admin_required
def admin_create_wine():
    try:
        insert_data = _wine_payload_from_fields(request.json.get('fields', {}))
        res = supabase_client.table("wines").insert(insert_data).execute()
        return jsonify({"status": "success", "data": res.data[0]})
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

def _commande_row_to_fields(r):
    """Format Supabase row → payload attendu par order.html / kitchen.html (clés Airtable-like).
    Le frontend fait `JSON.parse(f.Items)` donc on re-sérialise items en string."""
    items = r.get("items") or []
    if not isinstance(items, str):
        items = json.dumps(items, ensure_ascii=False)
    return {
        "id": r["id"],
        "fields": {
            "Ref":     r.get("ref"),
            "Table_N": r.get("table_n"),
            "Items":   items,
            "Total":   r.get("total"),
            "Statut":  r.get("statut"),
            "Heure":   r.get("heure"),
            "Service": r.get("service"),
            "Notes":   r.get("notes"),
        },
    }


@app.route('/api/orders', methods=['GET'])
def get_orders():
    try:
        if not supabase_client:
            return jsonify({"error": "Supabase non connecté"}), 500
        q = supabase_client.table("commandes").select("*").order("heure", desc=False)
        statut = request.args.get('statut')
        if statut:
            q = q.eq("statut", statut)
        res = q.execute()
        return jsonify([_commande_row_to_fields(r) for r in res.data])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/orders/table/<int:table_num>', methods=['GET'])
def get_table_orders(table_num):
    try:
        if not supabase_client:
            return jsonify({"error": "Supabase non connecté"}), 500
        # Toutes les commandes de la table sauf celles déjà servies/payées/annulées
        # PostgREST: `statut=not.in.(...)`
        res = (supabase_client.table("commandes")
               .select("*")
               .eq("table_n", table_num)
               .filter("statut", "not.in", "(Servi,Payé,Annulé)")
               .execute())
        return jsonify([_commande_row_to_fields(r) for r in res.data])
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
        payload = {
            "ref":     f"Table {table_num} - {now.strftime('%H:%M')}",
            "table_n": int(table_num),
            "items":   items,
            "total":   float(total),
            "statut":  "En attente",
            "heure":   now.isoformat(),
            "service": service,
            "notes":   notes,
        }
        res = supabase_client.table("commandes").insert(payload).execute()
        return jsonify({"status": "success", "record": _commande_row_to_fields(res.data[0])})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/api/orders/<record_id>', methods=['PATCH'])
def update_order_status(record_id):
    try:
        statut = (request.json or {}).get('statut')
        if not statut:
            return jsonify({"status": "error", "message": "Statut requis"}), 400
        supabase_client.table("commandes").update({"statut": statut}).eq("id", record_id).execute()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/api/billing/tables-ready', methods=['GET'])
def get_tables_ready_for_billing():
    """Retourne la liste des tables ayant au moins une commande Statut='Servi'."""
    try:
        res = (supabase_client.table("commandes")
               .select("table_n")
               .eq("statut", "Servi")
               .execute())
        tables = sorted({int(r["table_n"]) for r in res.data if r.get("table_n") is not None})
        return jsonify({"tables": tables})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/billing/table/<int:table_num>', methods=['GET'])
def get_billing_table(table_num):
    try:
        res = (supabase_client.table("commandes")
               .select("*")
               .eq("table_n", table_num)
               .eq("statut", "Servi")
               .execute())
        records = res.data
        commande_ids = [r["id"] for r in records]

        aggregated = {}
        for r in records:
            items = r.get("items") or []
            if isinstance(items, str):
                try: items = json.loads(items)
                except Exception: items = []
            for item in items:
                item_id = item.get('id', item.get('nom', ''))
                if item_id in aggregated:
                    aggregated[item_id]['qty'] += item.get('qty', 1)
                else:
                    cats = item.get('categories')
                    categorie = item.get('categorie') or (cats[0] if isinstance(cats, list) and cats else '')
                    aggregated[item_id] = {
                        'nom':       item.get('nom', ''),
                        'prix':      float(item.get('prix', 0)),
                        'qty':       item.get('qty', 1),
                        'categorie': categorie,
                    }

        return jsonify({
            "table": table_num,
            "commande_ids": commande_ids,
            "items": list(aggregated.values()),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/billing/close', methods=['POST'])
def close_billing():
    try:
        commande_ids = (request.json or {}).get('commande_ids', [])
        if not commande_ids:
            return jsonify({"status": "error", "message": "Aucune commande à clôturer"}), 400
        # Update en lot via filter `id in (...)`
        (supabase_client.table("commandes")
         .update({"statut": "Payé"})
         .in_("id", commande_ids)
         .execute())
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# --- ROUTES MENUS ÉVÉNEMENTS ---
# Stockés dans Supabase (table public.special_menus).

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
