import requests
import json
import time
import urllib.parse
import urllib3
import argparse

from common.utilities import print_json, get_token, get_config, CustomHelpFormatter
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
def start_charge(vin):
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
    log_error('start_charge(' + vin + '):', e)


##
# Function to send API call to stop charging a vehicle.
#
# author: mjhwa@yahoo.com
##
def stop_charge(vin):
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
    log_error('stop_charge(' + vin + '):', e)

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
# Sets the driver and/or passenger-side cabin temperature 
# (and other zones if sync is enabled).
#
# d_temp:  driver side temperature in C
# p_temp:  passenger side temperature in C
#
# author: mjhwa@yahoo.com
##
def set_temp(vin, d_temp, p_temp):
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
    log_error('set_temp(' + vin + '):', e)


##
# Sets seat heating. Requires preconditioning or climate keeper to be on.
#
# seat:  0: front left
#        1: front right
#        2: rear left
#        4: rear center
#        5: rear right
# setting:  0: off
#           1: low
#           2: medium
#           3: high
#
# author: mjhwa@yahoo.com
##
def set_seat_heating(vin, seat, setting):
  try:
    set_seat_temp(vin, 'heat', seat, setting)
  except Exception as e:
    log_error('set_seat_heating(' + vin + '):', e)


##
# Sets seat cooling. Requires preconditioning or climate keeper to be on.
#
# seat:  1: front left
#        2: front right
# setting:  0: off
#           1: low
#           2: medium
#           3: high
#
# author: mjhwa@yahoo.com
##
def set_seat_cooling(vin, seat, setting):
  try:
    set_seat_temp(vin, 'cool', seat, setting)
  except Exception as e:
    log_error('set_seat_cooling(' + vin + '):', e)


##
# Function to set vehicle seat heating or cooling level.
#
# author: mjhwa@yahoo.com
##
def set_seat_temp(vin, mode, seat, setting):
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
    log_error('set_seat_temp(' + vin + '):', e)


##
# Sets automatic seat heating and cooling. Requires preconditioning or 
# climate keeper to be on.
# 
# enable:  True/False (on/off)
# seat:  1: front left
#        2: front right
#
# author: mjhwa@yahoo.com
##
def set_seat_climate_auto(vin, enable, seat):
  try:  
    url = (BASE_PROXY_URL
           + '/vehicles/'
           + vin 
           + '/command/remote_auto_seat_climate_request')

    payload = {
      'auto_climate_on': enable,
      'auto_seat_position': seat
    }

    urllib3.disable_warnings(urllib3.exceptions.SubjectAltNameWarning)

    return requests.post(
      url, 
      json=payload, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN},
      verify=CERT
    )
  except Exception as e:
    log_error('set_seat_climate_auto(' + vin + '):', e)


##
# Sets steering wheel heating on/off. For vehicles that do not 
# support auto steering wheel heat. Requires preconditioning or 
# climate keeper to be on.
#
# enable:  True/False (on/off)
#
# author: mjhwa@yahoo.com
##
def set_steering_wheel_heating(vin, enable):
  try:  
    url = (BASE_PROXY_URL
           + '/vehicles/'
           + vin 
           + '/command/remote_steering_wheel_heater_request')

    payload = {
      'on': enable
    }

    urllib3.disable_warnings(urllib3.exceptions.SubjectAltNameWarning)

    return requests.post(
      url, 
      json=payload, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN},
      verify=CERT
    )
  except Exception as e:
    log_error('set_steering_wheel_heating(' + vin + '):', e)


##
# Function to start vehicle preconditioning.
#
# author: mjhwa@yahoo.com
##
def start_precondition(vin):
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
    log_error('start_precondition(' + vin + '):', e)


##
# Function to stop vehicle preconditioning.
#
# author: mjhwa@yahoo.com
##
def stop_precondition(vin):
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
    log_error('stop_precondition(' + vin + '):', e)


##
# Schedules a vehicle software update (over the air "OTA") to be 
# installed in the future.  Currently this works like the mobile 
# app where you cannot schedule a time in the future like you can 
# in the car.  You have to rely on crontab to mimic the behavior 
# to schedule in the future.
#
# offset_sec: seconds from now, e.g. 2 minutes from now = 60 * 2 = 120
#
# author: mjhwa@yahoo.com
##
def schedule_software_update(vin, time):
  try:
    url = (BASE_PROXY_URL
           + '/vehicles/' 
           + vin
           + '/command/schedule_software_update')

    payload = {
      'offset_sec': time
    }

    urllib3.disable_warnings(urllib3.exceptions.SubjectAltNameWarning)

    return requests.post(
      url, 
      json=payload, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN},
      verify=CERT
    )
  except Exception as e:
    log_error('schedule_software_update(' + vin + '):', e)


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


def main(parser):
  args = parser.parse_args()

  if (args.print):
    print_all_vehicle_data(args.print[0])
  else:
    parser.print_help()


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
                    prog='commandproxy.py',
                    description='API calls to modified tesla-http-proxy running on localhost.',
                    formatter_class=CustomHelpFormatter)
  parser.add_argument(
                      '-p', 
                      '--print', 
                      help='prints all the vehicle data; VIN is the Vehicle Identification Number you can find on the '
                           'car or in the mobile app',
                      nargs=1,
                      metavar='VIN'
                     )

  main(parser)