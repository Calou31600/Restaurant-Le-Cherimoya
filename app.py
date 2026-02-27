from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os
import sys
import cloudinary
import cloudinary.uploader

# Ajouter le dossier tools au path pour importer les moteurs
sys.path.append(os.path.join(os.getcwd(), 'tools'))

from main_engine import MainEngine

app = Flask(__name__, static_folder='.')
CORS(app)

engine = MainEngine()

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

@app.route('/admin')
def admin():
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
        
        if not all([name, date_str, time_str, service, covers]) or not (phone or email):
            return jsonify({"status": "error", "message": "Veuillez remplir tous les champs obligatoires (le nom et au moins un moyen de contact)."}), 400
            
        success, message = engine.booking.submit_reservation(name, phone, email, date_str, time_str, service, covers)
        if success:
            return jsonify({"status": "success", "message": message})
        else:
            return jsonify({"status": "error", "message": message}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/reservations/action/<record_id>/<status>', methods=['GET'])
def handle_reservation_action(record_id, status):
    """Gère les clics depuis l'email de notification."""
    success, message = engine.booking.update_reservation_status(record_id, status)
    
    # On renvoie une petite page HTML propre pour l'utilisateur (le resto)
    bg_color = "#28a745" if status == "Confirmée" else "#dc3545"
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #1a1a1a; color: white;">
        <div style="text-align: center; padding: 40px; border-radius: 10px; background: #2a2a2a; border: 1px solid {bg_color};">
            <h1 style="color: {bg_color};">{status} !</h1>
            <p>{message}</p>
            <p style="font-size: 0.9rem; color: #888;">Le client a été notifié par email.</p>
            <br>
            <a href="https://restaurant-le-cherimoya.vercel.app" style="color: white; text-decoration: none; border: 1px solid white; padding: 10px 20px; border-radius: 5px;">Retour au site</a>
        </div>
    </body>
    </html>
    """

# --- ROUTES ADMIN ---

@app.route('/api/admin/menu', methods=['GET'])
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

if __name__ == '__main__':
    # On tourne sur le port 5000 par défaut
    print("Serveur Le Cherimoya demarre sur http://localhost:5000")
    print("Dashboard accessible sur http://localhost:5000/admin")
    app.run(debug=True, port=5000)
