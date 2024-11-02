import requests
import json

url = "https://sdwan-dir.pres3-preprod.ekinops.io:8443/rest/json/v1.0/partner"

payload = json.dumps([
  {
    "address": "Ekinops, Newport, Wales",
    "admin_account": "JLK-python4@jlk-dot.com",
    "admin_password": "adm1n_P@ssword",
    "contact_name": "Jean-luc KRIKER",
    "contract_number": "10004",
    "description": "Created with Swagger",
    "email": "jean-luc.kriker@ekinops.com",
    "management_mtls": True,
    "name": "JLK-python4",
    "phone": "+441234567890"
  }
])
headers = {
  'vsts': 'F29YrNN95yhSOsF1Pc6pAPfCNlsIcX8T',
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)