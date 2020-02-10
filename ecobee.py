# ecobee Edge Data Store Historian
# Python script to read ecobee data remotely for a thermostat and write the data to EDS via OMF endpoint

import json
import requests
import shelve
import time
import sys

# Initialize token shelf on first run only
#apiKey = 'API KEY'
#api_token = 'API TOKEN'
#refresh_token = 'REFRESH TOKEN'
#thermostat_id = 'THERMOSTAT ID'
#config = shelve.open('ecobeeConfig',protocol=2)
#config['api_key'] = apiKey
#config['api_token'] = api_token
#config['refresh_token'] = refresh_token
#config['thermostat_id'] = thermostat_id
#config.close()

# ecobee API urls
api_url_base = 'https://api.ecobee.com/1/'
auth_url_base = 'https://api.ecobee.com/token'

# OSIsoft urls
eds_url_base = 'http://localhost:5590/api/v1/tenants/default/namespaces/default/omf/'
omfVersion = '1.1'

# Retrieve API key from shelf
config = shelve.open('ecobeeConfig',protocol=2)
apiKey = config['api_key']
thermostat_id = config['thermostat_id']
config.close()

# Function to get thermostat information
def get_thermostat_data():
    update_authorization()
    config = shelve.open('ecobeeConfig',protocol=2)
    current_api_token = config['api_token']
    config.close()

    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer {0}'.format(current_api_token)}

    # Get basic thermostat settings
    params = [{"selection":{"selectionType":"thermostats","selectionMatch":thermostat_id,"includeWeather":True,"includeRuntime":True,"includeSettings":True}}]
    params_json = json.dumps(params[0])

    api_url = '{0}thermostat?format=json&body='.format(api_url_base)

    response = requests.get(api_url + params_json, headers=headers)
    #print(response.text)

    if response.status_code == 200:
        resp_dict = json.loads(response.text)
        
        ecobeejsonData = json.dumps([{
            'containerid': 'DanHome',
            'values': [{
                'timestamp': resp_dict['thermostatList'][0]['runtime']['lastStatusModified'].replace(' ', 'T', 1) + 'Z',
                'lastModified': resp_dict['thermostatList'][0]['runtime']['lastModified'].replace(' ', 'T', 1) + 'Z',
                'connected': resp_dict['thermostatList'][0]['runtime']['connected'],
                'actualTemperature': resp_dict['thermostatList'][0]['runtime']['actualTemperature'],
                'actualHumidity': resp_dict['thermostatList'][0]['runtime']['actualHumidity'],
                'rawTemperature': resp_dict['thermostatList'][0]['runtime']['rawTemperature'],
                'desiredHeat': resp_dict['thermostatList'][0]['runtime']['desiredHeat'],
                'desiredCool': resp_dict['thermostatList'][0]['runtime']['desiredCool'],
                'desiredFanMode': resp_dict['thermostatList'][0]['runtime']['desiredFanMode'],
                'HVAC Mode': resp_dict['thermostatList'][0]['settings']['hvacMode'],
                'forecast_weatherSymbol': resp_dict['thermostatList'][0]['weather']['forecasts'][0]['weatherSymbol'],
                'forecast_condition': resp_dict['thermostatList'][0]['weather']['forecasts'][0]['condition'],
                'forecast_temperature': resp_dict['thermostatList'][0]['weather']['forecasts'][0]['temperature'],
                'forecast_pressure': resp_dict['thermostatList'][0]['weather']['forecasts'][0]['pressure'],
                'forecast_relativeHumidity': resp_dict['thermostatList'][0]['weather']['forecasts'][0]['relativeHumidity'],
                'forecast_dewpoint': resp_dict['thermostatList'][0]['weather']['forecasts'][0]['dewpoint'],
                'forecast_visibility': resp_dict['thermostatList'][0]['weather']['forecasts'][0]['visibility'],
                'forecast_windSpeed': resp_dict['thermostatList'][0]['weather']['forecasts'][0]['windSpeed'],
                'forecast_windGust': resp_dict['thermostatList'][0]['weather']['forecasts'][0]['windGust'],
                'forecast_windDirection': resp_dict['thermostatList'][0]['weather']['forecasts'][0]['windDirection'],
                'forecast_windBearing': resp_dict['thermostatList'][0]['weather']['forecasts'][0]['windBearing'],
                'forecast_pop': resp_dict['thermostatList'][0]['weather']['forecasts'][0]['pop'],
                'forecast_tempHigh': resp_dict['thermostatList'][0]['weather']['forecasts'][0]['tempHigh'],
                'forecast_tempLow': resp_dict['thermostatList'][0]['weather']['forecasts'][0]['tempLow'],
                'forecast_sky': resp_dict['thermostatList'][0]['weather']['forecasts'][0]['sky']
                }]
            }])

        return ecobeejsonData
    else:
        print("Communication Error: " + str(response.status_code))
        return -1

# Function to update ecobee API authorization
def update_authorization():
    # Make a call to see if the current token is valid
    config = shelve.open('ecobeeConfig',protocol=2)
    current_api_token = config['api_token']

    headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer {0}'.format(current_api_token)}

    # Get basic thermostat settings
    params = [{"selection": {"selectionType": "thermostats", "selectionMatch": thermostat_id, "includeSettings": True}}]
    params_json = json.dumps(params[0])

    api_url = '{0}thermostat?format=json&body='.format(api_url_base)

    response = requests.get(api_url + params_json, headers=headers)

    if response.status_code == 200:
        #print('Current token still valid, returning.')
        return ''
    else:
        current_refresh_token = config['refresh_token']
        params = {'grant_type': 'refresh_token',
                  'refresh_token': current_refresh_token,
                  'client_id': apiKey}

        response = requests.post(auth_url_base,params=params)

        if response.status_code == 200:
            #print('Token was expired, getting new token.')
            #print(response.text)
            config['api_token'] = response.json()['access_token']
            config['refresh_token'] = response.json()['refresh_token']
            config.close()
        else:
            config.close()
            #print(response.status_code)

# Define OMF Type
OMF_Ecobee_Type = json.dumps([{
    "id": "ecobee",
    "classification": "dynamic",
    "type": "object",
    "properties": {
        "timestamp": {
            "type": "string",
            "format": "date-time",
            "isindex": True
        },
        "lastModified": {
            "type": "string",
            "format": "date-time"
        },
        "connected": {
            "type": "string"
        },
        "actualTemperature": {
            "type": "number",
            "format": "float32"
        },
        "actualHumidity": {
            "type": "number",
            "format": "float32"
        },
        "rawTemperature": {
            "type": "number",
            "format": "float32"
        },
        "desiredHeat": {
            "type": "number",
            "format": "float32"
        },
        "desiredCool": {
            "type": "number",
            "format": "float32"
        },
        "desiredFanMode": {
            "type": "string"
        },
        "HVAC Mode": {
            "type": "string"
        },
        "forecast_weatherSymbol": {
            "type": "integer",
            "format": "int32"
        },
        "forecast_condition": {
            "type": "string"
        },
        "forecast_temperature": {
            "type": "number",
            "format": "float32"
        },
        "forecast_pressure": {
            "type": "number",
            "format": "float32"
        },
        "forecast_relativeHumidity": {
            "type": "number",
            "format": "float32"
        },
        "forecast_dewpoint": {
            "type": "number",
            "format": "float32"
        },
        "forecast_visibility": {
            "type": "number",
            "format": "float32"
        },
        "forecast_windSpeed": {
            "type": "number",
            "format": "float32"
        },
        "forecast_windGust": {
            "type": "number",
            "format": "float32"
        },
        "forecast_windDirection": {
            "type": "string"
        },
        "forecast_windBearing": {
            "type": "number",
            "format": "float32"
        },
        "forecast_pop": {
            "type": "number",
            "format": "float32"
        },
        "forecast_tempHigh": {
            "type": "number",
            "format": "float32"
        },
        "forecast_tempLow": {
            "type": "number",
            "format": "float32"
        },
        "forecast_sky": {
            "type": "integer",
            "format": "int32"
        }
    }
}])

# Define OMF Container
OMF_Ecobee_Container = json.dumps([{
    "id": "DanHome",
    "typeid": "ecobee"
}])

# Function to build headers for EDS post
def getHeaders(message_type='', action=''):
    msg_headers = {
        'Content-Type': 'application/json',
        'producertoken': 'x',
        'omfversion': str(omfVersion),
        'action': action,
        'messageformat': 'json',
        'messagetype': message_type
    }
    return msg_headers

# Function to post to EDS
def send_omf(endpoint_url, message_omf_json, message_type='', action='create'):
    headers = getHeaders(message_type, action)

    response = requests.post(endpoint_url, data=message_omf_json, headers=headers)

    if response.status_code >= 200 and response.status_code <= 204:
        print("EDS data written successfully. " + response.text)
        return response
    else:
        print("Communication Error: " + str(response.status_code)) + " " + response.text
        return response.status_code

# Create OMF Type
send_omf(eds_url_base, OMF_Ecobee_Type, 'type', 'create')

# Create OMF Container
send_omf(eds_url_base, OMF_Ecobee_Container, 'container', 'create')


# Run loop to send data over to EDS
while True:
    EDSContainerupdate = get_thermostat_data()
    send_omf(eds_url_base, EDSContainerupdate, 'data', 'create')
    time.sleep(90)
