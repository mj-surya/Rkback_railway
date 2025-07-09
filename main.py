from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes and origins

GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxq_G9QHiB2l40tS5zspn00aEyzO6fP0Wg-0zaGm8gdfnCTVUzg-c2I3RA5zSwg6Va_/exec"  # Replace with your actual URL

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

if __name__ == '__main__':
    app.run(debug=True)
