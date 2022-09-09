import requests
import json
import configparser
import os
import zoneinfo
import urllib3

from Crypto import encrypt, decrypt
from Influxdb import getDBClient
from Logger import logError
from datetime import datetime
from io import StringIO

TIME_ZONE = 'America/Los_Angeles'
PAC = zoneinfo.ZoneInfo(TIME_ZONE)
BASE_URL = 'https://powerwall/api/'


##
# Retrieves dictionary of local configuration values
# for direct access to the Tesla Energy Gateway.
#
# author: mjhwa@yahoo.com
##
def getLocalConfig():
  try:
    buffer = StringIO(
      decrypt(
        os.path.join(
          os.path.dirname(os.path.abspath(__file__)),
          'local_config.xor'
        ),
        os.path.join(
          os.path.dirname(os.path.abspath(__file__)),
          'config_key'
        )
      )
    )
    config = configparser.ConfigParser()
    config.sections()
    config.read_file(buffer)
    values = {s:dict(config.items(s)) for s in config.sections()}
    buffer.close()
    return values
  except Exception as e:
    logError('getLocalConfig(): ' + str(e))


config = getLocalConfig()
USERNAME = config['energy']['email']
PASSWORD = config['energy']['password']


##
# Writes live energy data to InfluxDB, accessed locally
# from the Tesla Energy Gateway.
#
# author: mjhwa@yahoo.com
##
def writeLocalLiveSiteTelemetry():
  try:
    data = getLocalSiteLiveStatus()

    json_body = []

    timestamp = data['solar']['last_communication_time']
    timestamp = timestamp[:26] + timestamp[-6:]  # Strip out the last 3 digits of nanoseconds
    json_body.append({
      'measurement': 'energy_live',
      'tags': {
        'source': 'solar_power'
      },
      'time': datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f%z'),
      'fields': {
        'value': float(data['solar']['instant_power'])
      }
    })

    timestamp = data['battery']['last_communication_time']
    timestamp = timestamp[:26] + timestamp[-6:]  # Strip out the last 3 digits of nanoseconds
    json_body.append({
      'measurement': 'energy_live',
      'tags': {
        'source': 'battery_power'
      },
      'time': datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f%z'),
      'fields': {
        'value': float(data['battery']['instant_power'])
      }
    })

    timestamp = data['site']['last_communication_time']
    timestamp = timestamp[:26] + timestamp[-6:]  # Strip out the last 3 digits of nanoseconds
    json_body.append({
      'measurement': 'energy_live',
      'tags': {
        'source': 'grid_power'
      },
      'time': datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f%z'),
      'fields': {
        'value': float(data['site']['instant_power'])
      }
    })

    timestamp = data['load']['last_communication_time']
    timestamp = timestamp[:26] + timestamp[-6:]  # Strip out the last 3 digits of nanoseconds
    json_body.append({
      'measurement': 'energy_live',
      'tags': {
        'source': 'load_power'
      },
      'time': datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f%z'),
      'fields': {
        'value': float(data['load']['instant_power'])
      }
    })

    json_body.append({
      'measurement': 'energy_live',
      'tags': {
        'source': 'percentage_charged'
      },
      'time': datetime.now().replace(tzinfo=PAC),  
      'fields': {
        'value': float(getLocalSOE()['percentage'])
      }
    })

    # Write to Influxdb
    client = getDBClient()
    client.switch_database('live')
    client.write_points(json_body)
    client.close()
  except Exception as e:
    logError('writeLocalLiveSiteTelemetry(): ' + str(e))


##
# Retrieves site energy data locally from the Tesla 
# Energy Gateway.
#
# author: mjhwa@yahoo.com
##
def getLocalSiteLiveStatus():
  try:
    url = (BASE_URL
            + 'meters/aggregates')

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    response = json.loads(
      requests.get(
        url,
        verify = False,
        headers={'authorization': 'Bearer ' + getLocalToken()['tesla']['token']}
      ).text
    )

    # Detect expired local token and re-auth
    if ('message' in response):
      if (response['message'] == 'Invalid bearer token'):
        authLocalToken()
        writeLocalLiveSiteTelemetry()

    return response
  except Exception as e:
    logError('getLocalSiteLiveStatus(): ' + str(e))


##
# Retrieves battery charge state locally from the Tesla 
# Energy Gateway.
#
# author: mjhwa@yahoo.com
##
def getLocalSOE():
  try:
    url = (BASE_URL
            + 'system_status/soe')

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    response = json.loads(
      requests.get(
        url,
        verify = False,
        headers={'authorization': 'Bearer ' + getLocalToken()['tesla']['token']}
      ).text
    )

    # Detect expired local token and re-auth
    if ('message' in response):
      if (response['message'] == 'Invalid bearer token'):
        authLocalToken()
        writeLocalLiveSiteTelemetry()

    return response
  except Exception as e:
    logError('getLocalSOE(): ' + str(e))


##
# Authenicates directly to the Tesla Energy Gateway to
# get a token for direct API calls.
#
# author: mjhwa@yahoo.com
##
def authLocalToken():
  try:
    url = (BASE_URL
            + 'login/Basic')

    payload = {
      'username': 'customer',
      'email': USERNAME,
      'password': PASSWORD,
      'force_sm_off': False
    }

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    response = json.loads(
      requests.post(
        url,
        verify = False,
        json=payload
      ).text
    )

    message =  '[tesla]\n'
    message += 'token=' + response['token'] + '\n'

    # Encrypt config file
    encrypt(
      message,
      os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'local_token.xor'
      ),
      os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'token_key'
      )
    )
  except Exception as e:
    logError('authLocalToken(): ' + str(e))


##
# Retrieves dictionary for a local token for direct 
# access to the Tesla Energy Gateway.
#
# author: mjhwa@yahoo.com
##
def getLocalToken():
  try:
    # Check for the file which stores the latest local token
    if os.path.exists(
      os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'local_token.xor'
      )    
    ) == False:
      authLocalToken()

    buffer = StringIO(
      decrypt(
        os.path.join(
          os.path.dirname(os.path.abspath(__file__)),
          'local_token.xor'
        ),
        os.path.join(
          os.path.dirname(os.path.abspath(__file__)),
          'token_key'
        )
      )
    )
    config = configparser.ConfigParser()
    config.sections()
    config.read_file(buffer)
    values = {s:dict(config.items(s)) for s in config.sections()}
    buffer.close()
    return values
  except Exception as e:
    logError('getLocalToken(): ' + str(e))


##
# Set on a 5 minute interval in crontab.
#
# author: mjhwa@yahoo.com
##
def main():
  writeLocalLiveSiteTelemetry()


if __name__ == "__main__":
  main()

