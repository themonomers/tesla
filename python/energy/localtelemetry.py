import json
import zoneinfo
import time

from common.utilities import get_config, get_local_config, get_local_token, auth_local_token, send_request
from common.influxdb import get_db_client
from common.logger import log_error
from datetime import datetime

TIME_ZONE = get_config()['general']['timezone']
PAC = zoneinfo.ZoneInfo(TIME_ZONE)
WAIT_TIME = 30  # seconds

LOCAL_TOKEN = get_local_token()['tesla']['token']
BASE_URL = get_local_config()['energy']['base_url']


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
    log_error('write_local_live_site_telemetry():', e)


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
    log_error('get_local_meters_aggregates():', e)


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
    log_error('get_local_system_status_soe():', e)


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
    log_error('get_local_system_status():', e)


def send_get(url):
  return send_request('GET', url, LOCAL_TOKEN, None, None)


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

