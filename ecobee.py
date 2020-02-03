# ecobee Edge Data Store Historian
# Simple Python script to read ecobee data remotely for a thermostat
#
import json
import requests
import shelve
import time
import sys

import subprocess
import pyecobee_lib

apiKey = 'API KEY'
api_token = 'YOUR API TOKEN'
refresh_token = 'YOUR REFRESH TOKEN'

# ecobee API Urls, thermostat identifier and default set temperature
api_url_base = 'https://api.ecobee.com/1/'
auth_url_base = 'https://api.ecobee.com/token'
thermostat_id = 'THERMOSTAT ID'
ecobeeActualTemp = 0
ecobeeSetTemp = 0
ecobeeMode = ''

#d = shelve.open('ecobeeConfig')
#d['api_token'] = api_token
#d['refresh_token'] = refresh_token
#d.close()

# Function to get thermostat information
def get_thermostat_info():
    update_authorization()
    config = shelve.open('ecobeeConfig')
    current_api_token = config['api_token']

    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer {0}'.format(current_api_token)}

    # Get basic thermostat settings
    params = [{"selection":{"selectionType":"thermostats","selectionMatch":thermostat_id,"includeRuntime":True}}]
    params_json = json.dumps(params[0])

    api_url = '{0}thermostat?format=json&body='.format(api_url_base)

    response = requests.get(api_url + params_json, headers=headers)

    if response.status_code == 200:
        resp_dict = json.loads(response.text)
        print('Name: ' + resp_dict['thermostatList'][0]['name'])
        print('Actual Temperature: ' + str(resp_dict['thermostatList'][0]['runtime']['actualTemperature']))
    else:
        return -1


# Function to get thermostat mode
def get_thermostat_mode():
    update_authorization()
    config = shelve.open('ecobeeConfig')
    current_api_token = config['api_token']

    headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer {0}'.format(current_api_token)}

    # Get basic thermostat settings
    params = [{"selection": {"selectionType": "thermostats", "selectionMatch": thermostat_id, "includeSettings": True}}]
    params_json = json.dumps(params[0])

    api_url = '{0}thermostat?format=json&body='.format(api_url_base)

    response = requests.get(api_url + params_json, headers=headers)

    if response.status_code == 200:
        resp_dict = json.loads(response.text)
        print('HVAC Mode: ' + str(resp_dict['thermostatList'][0]['settings']['hvacMode']))
        return str(resp_dict['thermostatList'][0]['settings']['hvacMode'])
    else:
        return ''

# Function to update ecobee API authorization
def update_authorization():
    # Make a call to see if the current token is valid
    config = shelve.open('ecobeeConfig')
    current_api_token = config['api_token']

    headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer {0}'.format(current_api_token)}

    # Get basic thermostat settings
    params = [{"selection": {"selectionType": "thermostats", "selectionMatch": thermostat_id, "includeSettings": True}}]
    params_json = json.dumps(params[0])

    api_url = '{0}thermostat?format=json&body='.format(api_url_base)

    response = requests.get(api_url + params_json, headers=headers)

    if response.status_code == 200:
        print('Current token still valid, returning.')
        return ''
    else:
        current_refresh_token = config['refresh_token']
        params = {'grant_type': 'refresh_token',
                  'refresh_token': current_refresh_token,
                  'client_id': apiKey}

        response = requests.post(auth_url_base,params=params)

        if response.status_code == 200:
            print('Token was expired, getting new token.')
            print(response.text)
            config['api_token'] = response.json()['access_token']
            config['refresh_token'] = response.json()['refresh_token']
            config.close()
        else:
            print(response.status_code)

# Function to get ecobee temperature data
def get_thermostat(getHoldTemperature):
    update_authorization()
    config = shelve.open('ecobeeConfig')
    current_api_token = config['api_token']

    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer {0}'.format(current_api_token)}

    params = [{"selection":{"selectionType":"thermostats","selectionMatch":thermostat_id},"functions":[{"type":"setHold","params":{"holdType":"nextTransition","heatHoldTemp":setHoldTemperature,"coolHoldTemp":setHoldTemperature}}]}]
    params_json = json.dumps(params[0])

    api_url = '{0}thermostat?format=json'.format(api_url_base)

    response = requests.post(api_url,params_json,headers=headers)

    if response.status_code == 200:
        print(response.text)
    else:
        print(response.status_code)

# Setup while loop precondition variables
prev_millis = int(round(time.time() * 1000))

