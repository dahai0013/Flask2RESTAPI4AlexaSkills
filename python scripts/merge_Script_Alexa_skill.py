from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import logging
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard
from ask_sdk_core.utils import is_request_type, is_intent_name

# Initialize Flask and SkillBuilder
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
sb = SkillBuilder()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load credentials from JSON file
with open('SDWAN_Director_credentials.json', 'r') as f:
    credentials = json.load(f)

API_URL = credentials['API_url']


# Function to get the VSTS token
def get_vsts_token():
    try:
        payload = json.dumps({
            "password": credentials['password'],
            "user": credentials['user']
        })
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        logger.info("Requesting token from SDWAN API...")
        response = requests.post(f"{API_URL}login", headers=headers, data=payload)

        if response.status_code == 200:
            token_data = response.json()
            logger.info("Token retrieved successfully")
            return token_data['vsts']
        else:
            logger.error(f"Failed to retrieve token: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error occurred while fetching token: {str(e)}")
        return None

# Function to add the token to the headers
def get_headers():
    token = get_vsts_token()
    if not token:
        raise Exception("Failed to get token")
    return {'vsts': token, 'Content-Type': 'application/json'}

# Flask route to delete a partner
@app.route('/delete_partner/<string:partner_id>', methods=['DELETE'])
def delete_partner(partner_id):
    try:
        headers = get_headers()
        response = requests.delete(f"{API_URL}partner/{partner_id}", headers=headers)
        if response.status_code == 200:
            return jsonify({"message": "Partner deleted successfully"}), 200
        else:
            logger.error(f"Failed to delete partner: {response.text}")
            return jsonify({"error": "Failed to delete partner", "details": response.text}), response.status_code
    except Exception as e:
        logger.error(f"Error in /delete_partner: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Flask route to list partners
@app.route('/list_partner', methods=['GET'])
def list_partner():
    try:
        headers = get_headers()
        response = requests.get(f"{API_URL}partner", headers=headers)
        data = response.json()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error in /list_partner: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Flask route to list POPs
@app.route('/list_pop', methods=['GET'])
def list_pop():
    try:
        headers = get_headers()
        response = requests.get(f"{API_URL}pop", headers=headers)
        data = response.json()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error in /list_pop: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Flask route to create a partner
@app.route('/create_partner', methods=['POST'])
def create_partner():
    partner_data = request.json
    logger.info(f"Received partner data: {partner_data}")

    try:
        headers = get_headers()
        response = requests.post(f"{API_URL}partner", headers=headers, json=[partner_data])

        if response.headers.get('Content-Type') == 'application/json':
            return jsonify(response.json()), response.status_code
        else:
            logger.error(f"Unexpected response format: {response.text}")
            return jsonify({'error': 'Unexpected response format'}), 500

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        return jsonify({'error': f"HTTP error occurred: {http_err}"}), 500

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Alexa Skill LaunchRequest Handler
@sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input: HandlerInput) -> Response:
    speech_text = "Welcome to Ekinops SD-WAN Director Alexa skill!, You can ask list partners or list pops."
    return (
        handler_input.response_builder
        .speak(speech_text)
        .set_card(SimpleCard("Welcome", speech_text))
        .set_should_end_session(False)
        .response
    )

# Intent handler for listing partners
@sb.request_handler(can_handle_func=is_intent_name("ListPartnerIntent"))
def list_partner_intent_handler(handler_input: HandlerInput) -> Response:
    response = list_partner()  # Call the Flask function directly
    data = response.get_json()  # Extract JSON content
    speech_text = f"Here are the partners: {data}"
    return handler_input.response_builder.speak(speech_text).response


@sb.request_handler(can_handle_func=is_intent_name("ListPartnerNameIntent"))
def list_partner_intent_handler(handler_input: HandlerInput) -> Response:
    response = list_partner()  # Call the Flask function directly
    data = response.get_json()  # Extract JSON content

    # Extract the names of the partners
    partner_names = [partner['name'] for partner in data]  # Assuming each partner has a 'name' attribute
    partner_count = len(partner_names)  # Count the number of partners

    if partner_count > 0:
        speech_text = f"There are {partner_count} partners, and the list is: {', '.join(partner_names)}."
    else:
        speech_text = "There are no partners found."

    return handler_input.response_builder.speak(speech_text).response


# Intent handler for listing POPs
@sb.request_handler(can_handle_func=is_intent_name("ListPOPIntent"))
def list_pop_intent_handler(handler_input: HandlerInput) -> Response:
    response = list_pop()  # Call the Flask function directly
    data = response.get_json()  # Extract JSON content
    speech_text = f"Here are the POPs: {data}"
    return handler_input.response_builder.speak(speech_text).response

# Intent handler for creating a partner
@sb.request_handler(can_handle_func=is_intent_name("CreatePartnerIntent"))
def create_partner_intent_handler(handler_input: HandlerInput) -> Response:
    partner_data = {"name": "New Partner"}  # Replace with actual data as needed
    with app.test_request_context(json=partner_data):  # Mimic Flask request context
        response = create_partner()
    data = response  # Extract JSON content
    speech_text = f"Partner creation response: {data}"
    return handler_input.response_builder.speak(speech_text).response

# Intent handler for deleting a partner
@sb.request_handler(can_handle_func=is_intent_name("DeletePartnerIntent"))
def delete_partner_intent_handler(handler_input: HandlerInput) -> Response:
    partner_id = "123"  # Replace with dynamic partner ID as needed
    with app.test_request_context():  # Mimic Flask request context
        response = delete_partner(partner_id)
    data = response  # Extract JSON content
    speech_text = f"Partner deletion response: {data}"
    return handler_input.response_builder.speak(speech_text).response

# Flask route for Alexa requests
@app.route('/alexa', methods=['POST'])
def alexa_handler():
    logger.debug("Received request: %s", request.json)
    response = sb.lambda_handler()(request.json, None)
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
