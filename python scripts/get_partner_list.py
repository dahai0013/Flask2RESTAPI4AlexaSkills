import requests
import json

url = "https://sdwan-dir.pres3-preprod.ekinops.io:8443/rest/json/v1.0/partner"

payload = {}
headers = {
  'vsts': 'TALEykh5ZI6CbGmLocTFRhOkfjnHKm2a'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)

# Parse the JSON string
data = json.loads(response.text)

# Print the JSON data in a pretty, multiline format
print(json.dumps(data, indent=4))