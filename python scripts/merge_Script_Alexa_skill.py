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

# # Updated route for listing sites
# @app.route('/list_site', methods=['GET'])
# def list_site():
#     #print("Rentering the list_site def")
#     try:
#         # Get partner and customer from query parameters
#         partner = request.args.get('partner', 'Pre_Sales')  # Default to 'Pre_Sales'
#         customer = request.args.get('customer', 'EKI_customer')  # Default to 'EKI_customer'
#
#         headers = get_headers()
#         # Use the partner and customer variables in the API URL
#         response = requests.get(f"{API_URL}{partner}/{customer}/site", headers=headers)
#         data = response.json()
#         #print("Response from API :", json.dumps(data, indent=4))
#
#         # Prepare list of device.serials
#         device_serials = []
#         for item in data:  # Iterating through the list of devices
#             device = item.get('device', {})
#             serial = device.get('serial', 'Unknown')
#             device_serials.append(serial)
#         print ( "device_serials ;",device_serials )
#
#         sites_info = []
#         for item in data:  # Iterating through the list of devices
#             device = item.get('site', {})
#             name = device.get('name', 'Unknown')
#             sites_info.append(name)
#         print ( "sites_info ;",sites_info )
#
#         #return jsonify(data)
#         # Return only the device.serial values
#         result = {'device_serials': device_serials, 'sites_info': sites_info}
#         return jsonify(result)
#
#     except Exception as e:
#         logger.error(f"Error in /list_site: {str(e)}")
#         return jsonify({'error': str(e)}), 500


@app.route('/list_site', methods=['GET'])
def list_site():
    # print("Entering the list_site function")
    try:
        # Get partner and customer from query parameters
        partner = request.args.get('partner', 'Pre_Sales')  # Default to 'Pre_Sales'
        customer = request.args.get('customer', 'EKI_customer')  # Default to 'EKI_customer'

        headers = get_headers()
        # Use the partner and customer variables in the API URL
        response = requests.get(f"{API_URL}{partner}/{customer}/site", headers=headers)
        data = response.json()
        # print("Response from API :", json.dumps(data, indent=4))

        # Prepare list of site information
        sites_info = []
        for item in data:  # Iterating through the list of sites
            site = item.get('site', {})
            name = site.get('name', 'Unknown')
            location = site.get('location', 'Unknown')
            device = item.get('device', {})
            serial = device.get('serial', 'Unknown')

            # Append site details and device serial in required order
            sites_info.append({
                'site_name': name,
                'site_location': location,
                'device_serial': serial
            })

        # Count the total number of sites
        total_sites = len(data)

        # Prepare the final result with the total count, site info, and full data
        result = {
            'total_sites': total_sites,
            'sites_info': sites_info,
            #'full_data': data
        }
        #
        # # Prepare the final result with the full JSON data as well
        # #result = {'sites_info': sites_info, 'full_data': data}
        # result = {'sites_info': sites_info}
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in /list_site: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/create_site', methods=['POST'])
def create_site():
    site_data = request.json
    #print(json.dumps(site_data, indent=4))
    #print ( f"{API_URL}Pre_sales/EKI_customer/site")

    try:
        # POST the site date
        logger.info("Sending site data to SDWAN Director API.")
        headers = get_headers()
        response = requests.post(f"{API_URL}Pre_sales/EKI_customer/site", headers=headers, json=[site_data])
        logger.info("Response status code: %d", response.status_code)
        logger.info("Response content: %s", response.text)  # Log the raw response content

        # Check if the response from SDWAN Director is JSON
        if response.headers.get('Content-Type') == 'application/json':
            return jsonify(response.json()), response.status_code
        else:
            logger.error("Expected JSON but received: %s", response.text)
            return jsonify({'error': 'Unexpected response format'}), 500

    except requests.exceptions.HTTPError as http_err:
        logger.error("HTTP error occurred: %s", http_err)
        return jsonify({'error': f"HTTP error occurred: {http_err}"}), 500


##############################################
#
#    Alexa configuration Part
#
##############################################

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
def list_partner_name_intent_handler(handler_input: HandlerInput) -> Response:
    # Print part of the JSON message receipt
    #print(json.dumps(handler_input.request_envelope, indent=4))
    # Print the JSON message receipt
    # try:
    #      print(json.dumps(vars(handler_input.request_envelope), indent=4))
    # except Exception as e:
    #      print(f"Can't print the JSON message: {e}")

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

# Catch-all intent handler for undefined intents
@sb.request_handler(can_handle_func=lambda handler_input: True)
def catch_all_intent_handler(handler_input: HandlerInput) -> Response:
    speech_text = "This intent does not exist on the backend server."
    return (
        handler_input.response_builder
        .speak(speech_text)
        .set_card(SimpleCard("Error", speech_text))
        .set_should_end_session(True)
        .response
    )

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
    # Extract the incoming Alexa request as a JSON object
    #print("Rx msg from Alexa in /alexa:", json.dumps(request.json, indent=4))

    # Extract intent type and name
    request_json = request.json
    request_type = request_json.get('request', {}).get('type', 'UnknownType')
    intent_name = request_json.get('request', {}).get('intent', {}).get('name', 'UnknownIntent')

    print(f"Intent Type: {request_type}")
    if request_type == "IntentRequest":
        print(f"Intent Name: {intent_name}")

    # Process the request
    response = sb.lambda_handler()(request_json, None)
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True)
