import requests
import json
import time
import urllib.parse
import urllib3

from common.utilities import print_json, get_token, get_config
from common.logger import log_error

ACCESS_TOKEN = get_token()['tesla']['access_token']
config = get_config()
BASE_PROXY_URL = config['tesla']['base_proxy_url']
CERT = config['tesla']['certificate']

WAIT_TIME = 30 


##
# Retrieves the vehicle data needed for higher level functions to drive 
# calcuations and actions.
# 
# author: mjhwa@yahoo.com 
##
def get_vehicle_data(vin):
  try:
    url = (BASE_PROXY_URL
           + '/vehicles/'
           + vin 
           + '/vehicle_data?endpoints='
           + urllib.parse.quote(
               'location_data;'
               + 'charge_state;'
               + 'climate_state;'
               + 'vehicle_state;'
               + 'gui_settings;'
               + 'vehicle_config;'
               + 'drive_state;'
               + 'charge_schedule_data'))

    urllib3.disable_warnings(urllib3.exceptions.SubjectAltNameWarning)

    response = requests.get(
      url, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN},
      verify=CERT
    )

    if response.status_code != 200:
      wake_vehicle(vin)
      time.sleep(WAIT_TIME)
      return get_vehicle_data(vin)

    return json.loads(response.text)
  except Exception as e:
    log_error('get_vehicle_data(' + vin + '):', e)


##
# Function to repeatedly run (after a certain wait time) to wake the vehicle up
# when it's asleep.
#
# author: mjhwa@yahoo.com
##
def wake_vehicle(vin):
  try:
    url = (BASE_PROXY_URL
           + '/vehicles/'
           + vin 
           + '/wake_up')

    urllib3.disable_warnings(urllib3.exceptions.SubjectAltNameWarning)

    return requests.post(
      url, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN},
      verify=CERT
    )
  except Exception as e:
    log_error('wake_vehicle(' + vin + '):', e)


##
# Function to send API call to start charging a vehicle.
#
# author: mjhwa@yahoo.com
##
def start_charge_vehicle(vin):
  try:
    url = (BASE_PROXY_URL
           + '/vehicles/'
           + vin
           + '/command/charge_start')

    urllib3.disable_warnings(urllib3.exceptions.SubjectAltNameWarning)

    return requests.post(
      url,
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN},
      verify=CERT
    )
  except Exception as e:
    log_error('start_charge_vehicle(' + vin + '):', e)


##
# Function to send API call to stop charging a vehicle.
#
# author: mjhwa@yahoo.com
##
def stop_charge_vehicle(vin):
  try:
    url = (BASE_PROXY_URL
           + '/vehicles/'
           + vin
           + '/command/charge_stop')

    urllib3.disable_warnings(urllib3.exceptions.SubjectAltNameWarning)

    return requests.post(
      url,
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN},
      verify=CERT
    )
  except Exception as e:
    log_error('stop_charge_vehicle(' + vin + '):', e)

##
# Uses new endpoint to add a schedule for vehicle charging. 
# Scheduled Time is in minutes, e.g. 7:30 AM = 
# (7 * 60) + 30 = 450
#
# author: mjhwa@yahoo.com
##
def add_charge_schedule(vin, lat, lon, start_time, id):
  try:
    url = (BASE_PROXY_URL
           + '/vehicles/'
           + vin 
           + '/command/add_charge_schedule')

    payload = {
      'days_of_week': 'All',
      'enabled': True,
      'start_enabled': True,
      'end_enabled': False,
      'lat': lat,
      'lon': lon,
      'start_time': start_time,
      'one_time': False,
      'id': id
    }

    urllib3.disable_warnings(urllib3.exceptions.SubjectAltNameWarning)

    return requests.post(
      url, 
      json=payload, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN},
      verify=CERT
    )
  except Exception as e:
    log_error('add_charge_schedule(' + vin + '):', e)


##
# Uses new endpoint to remove a schedule for vehicle charging. 
#
# author: mjhwa@yahoo.com
##
def remove_charge_schedule(vin, id):
  try:
    url = (BASE_PROXY_URL
           + '/vehicles/'
           + vin 
           + '/command/remove_charge_schedule')

    payload = {
      'id': id
    }

    urllib3.disable_warnings(urllib3.exceptions.SubjectAltNameWarning)

    return requests.post(
      url, 
      json=payload, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN},
      verify=CERT
    )
  except Exception as e:
    log_error('remove_charge_schedule(' + vin + '):', e)
  

##
# Per Tesla (https://developer.tesla.com/docs/fleet-api/endpoints/vehicle-commands#set-scheduled-charging):  
# This endpoint is not recommended beginning with firmware version 2024.26.
#
# Sends command and parameter to set a specific vehicle to charge
# at a scheduled time.  Scheduled Time is in minutes, e.g. 7:30 AM = 
# (7 * 60) + 30 = 450
#
# author: mjhwa@yahoo.com
##
def set_scheduled_charging(vin, time):
  try:
    url = (BASE_PROXY_URL
           + '/vehicles/'
           + vin 
           + '/command/set_scheduled_charging')

    payload = {
      'enable': True,
      'time': time
    }

    urllib3.disable_warnings(urllib3.exceptions.SubjectAltNameWarning)

    return requests.post(
      url, 
      json=payload, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN},
      verify=CERT
    )
  except Exception as e:
    log_error('set_scheduled_charging(' + vin + '):', e)


##
# Function to set vehicle temperature.
#
# author: mjhwa@yahoo.com
##
def set_car_temp(vin, d_temp, p_temp):
  try:
    url = (BASE_PROXY_URL
           + '/vehicles/'
           + vin 
           + '/command/set_temps')

    payload = {
      'driver_temp': d_temp,
      'passenger_temp': p_temp
    }

    urllib3.disable_warnings(urllib3.exceptions.SubjectAltNameWarning)

    return requests.post(
      url, 
      json=payload, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN},
      verify=CERT
    )
  except Exception as e:
    log_error('set_car_temp(' + vin + '):', e)


##
# Function to set vehicle seat heater level.
#
# author: mjhwa@yahoo.com
##
def set_car_seat_heating(vin, seat, setting):
  try:
    set_car_seat_temp(vin, 'heat', seat, setting)
  except Exception as e:
    log_error('set_car_seat_heating(' + vin + '):', e)


##
# Function to set vehicle seat cooler level.
#
# author: mjhwa@yahoo.com
##
def set_car_seat_cooling(vin, seat, setting):
  try:
    set_car_seat_temp(vin, 'cool', seat, setting)
  except Exception as e:
    log_error('set_car_seat_cooling(' + vin + '):', e)


##
# Function to set vehicle seat heating or cooling level.
#
# author: mjhwa@yahoo.com
##
def set_car_seat_temp(vin, mode, seat, setting):
  try:
    url = (BASE_PROXY_URL
           + '/vehicles/'
           + vin)
    
    if mode == 'heat':
      url += '/command/remote_seat_heater_request'

      payload = {
        'seat_position': seat,
        'level': setting
      }
    elif mode == 'cool':
      url += '/command/remote_seat_cooler_request'

      payload = {
        'seat_position': seat,
        'seat_cooler_level': setting
      }
    else:
      raise Exception('No mode given.')

    urllib3.disable_warnings(urllib3.exceptions.SubjectAltNameWarning)

    return requests.post(
      url, 
      json=payload, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN},
      verify=CERT
    )
  except Exception as e:
    log_error('set_car_seat_temp(' + vin + '):', e)


##
# Function to start vehicle preconditioning.
#
# author: mjhwa@yahoo.com
##
def precondition_car_start(vin):
  try:  
    url = (BASE_PROXY_URL
           + '/vehicles/'
           + vin 
           + '/command/auto_conditioning_start')

    urllib3.disable_warnings(urllib3.exceptions.SubjectAltNameWarning)

    return requests.post(
      url, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN},
      verify=CERT
    )
  except Exception as e:
    log_error('precondition_car_start(' + vin + '):', e)


##
# Function to stop vehicle preconditioning.
#
# author: mjhwa@yahoo.com
##
def precondition_car_stop(vin):
  try:
    url = (BASE_PROXY_URL
           + '/vehicles/'
           + vin
           + '/command/auto_conditioning_stop')
    
    urllib3.disable_warnings(urllib3.exceptions.SubjectAltNameWarning)

    return requests.post(
      url, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN},
      verify=CERT
    )
  except Exception as e:
    log_error('precondition_car_stop(' + vin + '):', e)

##
# Loops through all vehicle data and prints to screen.  
#
# author: mjhwa@yahoo.come
##
def print_all_vehicle_data(vin):
  try:
    data = get_vehicle_data(vin)

    if ('error' in data):
      raise Exception (data['error'])

    print_json(data, 0)
  except Exception as e:
    log_error('print_all_vehicle_data(' + vin + '):', e)
    wake_vehicle(vin)
    print_all_vehicle_data(vin)


def main():
  vin = input('print_all_vehicle_data VIN: ')
  print_all_vehicle_data(vin)


if __name__ == "__main__":
  main()
