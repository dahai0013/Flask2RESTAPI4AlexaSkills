from flask import Flask, jsonify, request
import requests
import json

app = Flask(__name__)

SDWAN_URL = "https://sdwan-dir.pres3-preprod.ekinops.io:8443/rest/json/v1.0/partner"
HEADERS = {
    'vsts': 'TALEykh5ZI6CbGmLocTFRhOkfjnHKm2a'
}

# Route to list partners
@app.route('/list_partner', methods=['GET'])
def list_partner():
    try:
        response = requests.get(SDWAN_URL, headers=HEADERS)
        data = response.json()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Future route for creating a partner
@app.route('/create_partner', methods=['POST'])
def create_partner():
    partner_data = request.json
    # For now, we'll just return the received data
    return jsonify(partner_data)

if __name__ == '__main__':
    app.run(debug=True)
