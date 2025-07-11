from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
import json

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
DATA_FILE = 'data.json'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
OFFER_FILE = 'offers.json'

# Ensure offers.json exists
if not os.path.exists(OFFER_FILE):
    with open(OFFER_FILE, 'w') as f:
        json.dump({"latest_offer": ""}, f)


GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxq_G9QHiB2l40tS5zspn00aEyzO6fP0Wg-0zaGm8gdfnCTVUzg-c2I3RA5zSwg6Va_/exec"

# Ensure data.json exists
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

# --- Existing Status Update API ---
@app.route('/update-status', methods=['POST'])
def update_status():
    try:
        data = request.get_json()
        email = data.get('email')
        id = data.get('id')
        status = data.get('status')

        if not status or (not email and not id):
            return jsonify({"error": "Missing 'status' or identifier (email or id)"}), 400

        payload = {
            "status": status,
            "email": email,
            "id": id
        }

        res = requests.post(GOOGLE_SCRIPT_URL, json=payload)
        return jsonify(res.json()), res.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- New API to Upload Content (Category + Image/Video File) ---
@app.route('/upload-content', methods=['POST'])
def upload_content():
    try:
        category = request.form.get('category')
        file = request.files.get('file')

        if not category or not file:
            return jsonify({"error": "Missing category or file"}), 400

        filename = file.filename
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)

        # Save category & filename mapping in data.json
        with open(DATA_FILE, 'r+') as f:
            data = json.load(f)
            data.append({"category": category, "filename": filename,"url": f"/media/{filename}"})
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

        return jsonify({
            "message": "File uploaded successfully",
            "filename": filename,
            "category": category,
            "url": f"/media/{filename}"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- New API to Serve Uploaded Media (for UI rendering) ---
@app.route('/media/<filename>', methods=['GET'])
def serve_media(filename):
    try:
        return send_from_directory(UPLOAD_FOLDER, filename)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404


# --- Optional: Get all uploaded entries ---
@app.route('/media-list', methods=['GET'])
def list_uploaded_files():
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- API to Delete an Uploaded File and Its JSON Entry ---
@app.route('/delete-content', methods=['POST'])
def delete_content():
    try:
        data = request.get_json()
        filename = data.get('filename')

        if not filename:
            return jsonify({"error": "Missing 'filename'"}), 400

        # Delete file from uploads folder
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            return jsonify({"error": "File not found on disk"}), 404

        # Remove entry from data.json
        with open(DATA_FILE, 'r+') as f:
            records = json.load(f)
            updated_records = [entry for entry in records if entry.get('filename') != filename]
            f.seek(0)
            json.dump(updated_records, f, indent=2)
            f.truncate()

        return jsonify({"message": f"{filename} deleted successfully."}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# --- API to Add or Update Offer Text ---
@app.route('/add-offer', methods=['POST'])
def add_offer():
    try:
        data = request.get_json()
        offer_text = data.get('offer')

        if not offer_text:
            return jsonify({"error": "Missing 'offer' text"}), 400

        with open(OFFER_FILE, 'w') as f:
            json.dump({"latest_offer": offer_text}, f, indent=2)

        return jsonify({"message": "Offer updated successfully", "offer": offer_text}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- API to Get the Latest Offer Text ---
@app.route('/get-offer', methods=['GET'])
def get_offer():
    try:
        with open(OFFER_FILE, 'r') as f:
            offer_data = json.load(f)
        return jsonify(offer_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Use PORT env variable or fallback to 5000
    app.run(host='0.0.0.0', port=port, debug=True)
