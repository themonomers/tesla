import requests
import json
import configparser
import os
import zoneinfo
import urllib3
import time

from Crypto import encrypt, decrypt
from Influxdb import getDBClient
from Logger import logError
from Utilities import getConfig
from datetime import datetime
from io import StringIO

TIME_ZONE = getConfig()['general']['timezone']
PAC = zoneinfo.ZoneInfo(TIME_ZONE)
WAIT_TIME = 30  # seconds


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
          'tesla_private_key.pem'
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
BASE_URL = config['energy']['base_url']

##
# Writes live energy data to InfluxDB, accessed locally
# from the Tesla Energy Gateway.
#
# author: mjhwa@yahoo.com
##
def writeLocalLiveSiteTelemetry():
  try:
    data = getLocalMetersAggregates()

    json_body = []

    json_body.append({
      'measurement': 'energy_live',
      'tags': {
        'source': 'solar_power'
      },
      'time': timestampSplit(data['solar']['last_communication_time']),
      'fields': {
        'value': float(data['solar']['instant_power'])
      }
    })

    json_body.append({
      'measurement': 'energy_live',
      'tags': {
        'source': 'battery_power'
      },
      'time': timestampSplit(data['battery']['last_communication_time']),
      'fields': {
        'value': float(data['battery']['instant_power'])
      }
    })

    json_body.append({
      'measurement': 'energy_live',
      'tags': {
        'source': 'grid_power'
      },
      'time': timestampSplit(data['site']['last_communication_time']),
      'fields': {
        'value': float(data['site']['instant_power'])
      }
    })

    json_body.append({
      'measurement': 'energy_live',
      'tags': {
        'source': 'load_power'
      },
      'time': timestampSplit(data['load']['last_communication_time']),
      'fields': {
        'value': float(data['load']['instant_power'])
      }
    })

    timestamp = datetime.now().replace(tzinfo=PAC).strftime('%Y-%m-%dT%H:%M:%S.%f%z')
    json_body.append({
      'measurement': 'energy_live',
      'tags': {
        'source': 'percentage_charged'
      },
      'time': timestampSplit(timestamp),  
      'fields': {
        'value': float(getLocalSystemStatusSOE()['percentage'])
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
def getLocalMetersAggregates():
  try:
    url = (BASE_URL
            + '/meters/aggregates')

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    response = requests.get(
        url,
        verify = False,
        headers={'authorization': 'Bearer ' + getLocalToken()['tesla']['token']}
    )

    # Detect expired local token and re-auth
    resp = json.loads(response.text)
    if ('message' in resp):
      if (resp['message'] == 'Invalid bearer token'):
        authLocalToken()
        writeLocalLiveSiteTelemetry()
    elif (response.status_code != 200):
      time.sleep(WAIT_TIME)
      return getLocalMetersAggregates()

    return resp
  except Exception as e:
    logError('getLocalMetersAggregates(): ' + str(e))


##
# Retrieves battery charge state locally from the Tesla 
# Energy Gateway.
#
# author: mjhwa@yahoo.com
##
def getLocalSystemStatusSOE():
  try:
    url = (BASE_URL
            + '/system_status/soe')

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    response = requests.get(
        url,
        verify = False,
        headers={'authorization': 'Bearer ' + getLocalToken()['tesla']['token']}
    )

    # Detect expired local token and re-auth
    resp = json.loads(response.text)    
    if ('message' in resp):
      if (resp['message'] == 'Invalid bearer token'):
        authLocalToken()
        writeLocalLiveSiteTelemetry()
    elif (response.status_code != 200):
      time.sleep(WAIT_TIME)
      return getLocalSystemStatusSOE()

    return resp
  except Exception as e:
    logError('getLocalSystemStatusSOE(): ' + str(e))


##
# Provides information on batteries and inverters.
#
# author: mjhwa@yahoo.com
##
def getLocalSystemStatus():
  try:
    url = (BASE_URL
            + '/system_status')

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    response = requests.get(
        url,
        verify = False,
        headers={'authorization': 'Bearer ' + getLocalToken()['tesla']['token']}
    )

    # Detect expired local token and re-auth
    resp = json.loads(response.text)    
    if ('message' in resp):
      if (resp['message'] == 'Invalid bearer token'):
        authLocalToken()
        writeLocalLiveSiteTelemetry()
    elif (response.status_code != 200):
      time.sleep(WAIT_TIME)
      return getLocalSystemStatus()

    return resp
  except Exception as e:
    logError('getLocalSystemStatus(): ' + str(e))


##
# Removes the nanoseconds in the timestamp provided by the
# local Tesla Gateway that sometimes gives less digits and
# breaks the timestamp string format function.
#
# author: mjhwa@yahoo.com
##
def timestampSplit(timestamp):
  if (timestamp.split('.', 1)[1].find('-') > -1):
    timestamp = timestamp.split('.', 1)[0] + '-' + timestamp.split('.', 1)[1].split('-', 1)[1]
  elif (timestamp.split('.', 1)[1].find('+') > -1):
    timestamp = timestamp.split('.', 1)[0] + '+' + timestamp.split('.', 1)[1].split('+', 1)[1]
  
  return datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S%z')


##
# Authenicates directly to the Tesla Energy Gateway to
# get a token for direct API calls.
#
# author: mjhwa@yahoo.com
##
def authLocalToken():
  try:
    url = (BASE_URL
            + '/login/Basic')

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
        'tesla_private_key.pem'
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
          'tesla_private_key.pem'
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

