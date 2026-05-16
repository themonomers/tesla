import requests
import urllib3
import json
import zoneinfo
import time
import os
import configparser

from common.logutil import log
from common.crypto import encrypt, decrypt
from common.influxdb import get_db_client
from datetime import datetime
from io import StringIO

WAIT_TIME = 30  # seconds


##
# Retrieves dictionary of local configuration values
# for direct access to the Tesla Energy Gateway.
#
# author: mjhwa@yahoo.com
##
def get_local_config():
  try:
    buffer = StringIO(
      decrypt(
        os.path.join(
          os.path.dirname(os.path.abspath(__file__)),
          'local_config.xor'
        ),
        os.path.join(
          os.path.dirname(os.path.abspath(__file__)),
          '../common/tesla_private_key.pem'
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
    log().error('get_local_config(): ' + str(e))

local_config = get_local_config()
USERNAME = local_config['energy']['email']
PASSWORD = local_config['energy']['password']
BASE_URL = local_config['energy']['base_url']
TIME_ZONE = local_config['general']['timezone']
PAC = zoneinfo.ZoneInfo(TIME_ZONE)


##
# Retrieves dictionary for a local token for direct 
# access to the Tesla Energy Gateway.
#
# author: mjhwa@yahoo.com
##
def get_local_token():
  try:
    # Check for the file which stores the latest local token
    if os.path.exists(
      os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'local_token.xor'
      )    
    ) == False:
      auth_local_token()

    buffer = StringIO(
      decrypt(
        os.path.join(
          os.path.dirname(os.path.abspath(__file__)),
          'local_token.xor'
        ),
        os.path.join(
          os.path.dirname(os.path.abspath(__file__)),
          '../common/tesla_private_key.pem'
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
    log().error('get_local_token(): ' + str(e))

LOCAL_TOKEN = get_local_token()['tesla']['token']


##
# Authenicates directly to the Tesla Energy Gateway to
# get a token for direct API calls.
#
# author: mjhwa@yahoo.com
##
def auth_local_token():
  try:
    url = (BASE_URL
            + '/login/Basic')

    payload = {
      'username': 'customer',
      'email': USERNAME,
      'password': PASSWORD,
      'force_sm_off': False
    }

    response = json.loads(send_request('POST', url, LOCAL_TOKEN, payload).text)

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
        '../common/tesla_private_key.pem'
      )
    )
  except Exception as e:
    log().error('auth_local_token(): ' + str(e))


##
# Writes live energy data to InfluxDB, accessed locally
# from the Tesla Energy Gateway.
#
# author: mjhwa@yahoo.com
##
def write_local_live_site_telemetry():
  try:
    data = get_local_meters_aggregates()

    json_body = []

    json_body.append({
      'measurement': 'energy_live',
      'tags': {
        'source': 'solar_power'
      },
      'time': split_timestamp(data['solar']['last_communication_time']),
      'fields': {
        'value': float(data['solar']['instant_power'])
      }
    })

    json_body.append({
      'measurement': 'energy_live',
      'tags': {
        'source': 'battery_power'
      },
      'time': split_timestamp(data['battery']['last_communication_time']),
      'fields': {
        'value': float(data['battery']['instant_power'])
      }
    })

    json_body.append({
      'measurement': 'energy_live',
      'tags': {
        'source': 'grid_power'
      },
      'time': split_timestamp(data['site']['last_communication_time']),
      'fields': {
        'value': float(data['site']['instant_power'])
      }
    })

    json_body.append({
      'measurement': 'energy_live',
      'tags': {
        'source': 'load_power'
      },
      'time': split_timestamp(data['load']['last_communication_time']),
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
      'time': split_timestamp(timestamp),  
      'fields': {
        'value': float(get_local_system_status_soe()['percentage'])
      }
    })

    # Write to Influxdb
    client = get_db_client()
    client.switch_database('live')
    client.write_points(json_body)
    client.close()
  except Exception as e:
    log().error('write_local_live_site_telemetry(): ' + str(e))


##
# Retrieves site energy data locally from the Tesla 
# Energy Gateway.
#
# author: mjhwa@yahoo.com
##
def get_local_meters_aggregates():
  try:
    url = (BASE_URL
            + '/meters/aggregates')

    response = send_get(url)

    # Detect expired local token and re-auth
    resp = json.loads(response.text)
    if ('message' in resp):
      if (resp['message'] == 'Invalid bearer token'):
        auth_local_token()
        write_local_live_site_telemetry()
    elif (response.status_code != 200):
      time.sleep(WAIT_TIME)
      return get_local_meters_aggregates()

    return resp
  except Exception as e:
    log().error('get_local_meters_aggregates(): ' + str(e))


##
# Retrieves battery charge state locally from the Tesla 
# Energy Gateway.
#
# author: mjhwa@yahoo.com
##
def get_local_system_status_soe():
  try:
    url = (BASE_URL
            + '/system_status/soe')

    response = send_get(url)

    # Detect expired local token and re-auth
    resp = json.loads(response.text)    
    if ('message' in resp):
      if (resp['message'] == 'Invalid bearer token'):
        auth_local_token()
        write_local_live_site_telemetry()
    elif (response.status_code != 200):
      time.sleep(WAIT_TIME)
      return get_local_system_status_soe()

    return resp
  except Exception as e:
    log().error('get_local_system_status_soe(): ' + str(e))


##
# Provides information on batteries and inverters.
#
# author: mjhwa@yahoo.com
##
def get_local_system_status():
  try:
    url = (BASE_URL
            + '/system_status')

    response = send_get(url)

    # Detect expired local token and re-auth
    resp = json.loads(response.text)    
    if ('message' in resp):
      if (resp['message'] == 'Invalid bearer token'):
        auth_local_token()
        write_local_live_site_telemetry()
    elif (response.status_code != 200):
      time.sleep(WAIT_TIME)
      return get_local_system_status()

    return resp
  except Exception as e:
    log().error('get_local_system_status(): ' + str(e))


def send_get(url):
  return send_request('GET', url, LOCAL_TOKEN, None)


###
# Centralize repetitive HTTP Request calls.
#
# author: mjhwa@yahoo.com
##
def send_request(method, url, token, payload):
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

  return requests.request(
    method,
    url, 
    **({'json': payload} if payload else {}),
    headers={'authorization': 'Bearer ' + token},
    verify=False
  )


##
# Removes the nanoseconds in the timestamp provided by the
# local Tesla Gateway that sometimes gives less digits and
# breaks the timestamp string format function.
#
# author: mjhwa@yahoo.com
##
def split_timestamp(timestamp):
  if (timestamp.split('.', 1)[1].find('-') > -1):
    timestamp = timestamp.split('.', 1)[0] + '-' + timestamp.split('.', 1)[1].split('-', 1)[1]
  elif (timestamp.split('.', 1)[1].find('+') > -1):
    timestamp = timestamp.split('.', 1)[0] + '+' + timestamp.split('.', 1)[1].split('+', 1)[1]
  
  return datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S%z')


##
# Set on a 5 minute interval in crontab.
#
# author: mjhwa@yahoo.com
##
def main():
  write_local_live_site_telemetry()


if __name__ == "__main__":
  main()