import json
import time
import urllib.parse
import argparse

from common.configutil import get_config
from common.logutil import log
from common.argutil import CustomHelpFormatter
from common.utilities import print_json, send_request, get_uri
from common.tokenutil import get_token
from common.fileutil import get_filepath

ACCESS_TOKEN = get_token()['tesla']['access_token']

config = get_config()
M3_VIN = config['vehicle']['m3_vin']
MX_VIN = config['vehicle']['mx_vin']
BASE_PROXY_URL = get_uri('tesla', 'baseProxyUrl')
CERT = get_filepath('secrets', 'teslaCert')

WAIT_TIME = 30 


##
# Retrieves the vehicle data needed for higher level functions to drive 
# calcuations and actions.
# 
# author: mjhwa@yahoo.com 
##
def get_vehicle_data(vin):
  url = (BASE_PROXY_URL
          + '/api/1/vehicles/'
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

  response = send_get(url)

  if response.status_code != 200:
    wake_vehicle(vin)
    time.sleep(WAIT_TIME)
    return get_vehicle_data(vin)

  return json.loads(response.text)


##
# Function to repeatedly run (after a certain wait time) to wake the vehicle up
# when it's asleep.
#
# author: mjhwa@yahoo.com
##
def wake_vehicle(vin):
  url = (BASE_PROXY_URL
          + '/api/1/vehicles/'
          + vin 
          + '/wake_up')

  return send_post(url, None)


##
# Function to send API call to start charging a vehicle.
#
# author: mjhwa@yahoo.com
##
def start_charge(vin):
  return send_post(get_url(vin, 'charge_start'), None)


##
# Function to send API call to stop charging a vehicle.
#
# author: mjhwa@yahoo.com
##
def stop_charge(vin):
  return send_post(get_url(vin, 'charge_stop'), None)


##
# Uses new endpoint to add a schedule for vehicle charging. 
# Scheduled Time is in minutes, e.g. 7:30 AM = 
# (7 * 60) + 30 = 450
#
# author: mjhwa@yahoo.com
##
def add_charge_schedule(vin, lat, lon, start_time, id):
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

  return send_post(get_url(vin, 'add_charge_schedule'), payload)


##
# Uses new endpoint to remove a schedule for vehicle charging. 
#
# author: mjhwa@yahoo.com
##
def remove_charge_schedule(vin, id):
  payload = {
    'id': id
  }

  return send_post(get_url(vin, 'remove_charge_schedule'), payload)
  

##
# Sends command to set the charging amps for a specified vehicle.
#
# author: mjhwa@yahoo.com
##
def set_charging_amps(vin, amps):
  payload = {
    'charging_amps': amps
  }

  return send_post(get_url(vin, 'set_charging_amps'), payload)


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
  payload = {
    'driver_temp': d_temp,
    'passenger_temp': p_temp
  }

  return send_post(get_url(vin, 'set_temps'), payload)


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
  payload = {
    'seat_position': seat,
    'level': setting
  }

  return send_post(get_url(vin, 'remote_seat_heater_request'), payload)


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
  payload = {
    'seat_position': seat,
    'seat_cooler_level': setting
  }

  return send_post(get_url(vin, 'remote_seat_cooler_request'), payload)


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
  payload = {
    'auto_climate_on': enable,
    'auto_seat_position': seat
  }

  return send_post(get_url(vin, 'remote_auto_seat_climate_request'), payload)


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
  payload = {
    'on': enable
  }

  return send_post(get_url(vin, 'remote_steering_wheel_heater_request'), payload)


##
# Function to start vehicle preconditioning.
#
# author: mjhwa@yahoo.com
##
def start_precondition(vin):
  return send_post(get_url(vin, 'auto_conditioning_start'), None)


##
# Function to stop vehicle preconditioning.
#
# author: mjhwa@yahoo.com
##
def stop_precondition(vin):
  return send_post(get_url(vin, 'auto_conditioning_stop'), None)


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
def schedule_software_update(vin, offset_sec):
  try:
    payload = {
      'offset_sec': offset_sec
    }

    response = send_post(get_url(vin, 'schedule_software_update'), payload)
    if response.status_code != 200:
      wake_vehicle(vin)
      time.sleep(WAIT_TIME)
      return schedule_software_update(vin, offset_sec)

    return response 
  except Exception as e:
    log().error('schedule_software_update(' + vin + '): ' + str(e))


###
# Centralize repetitive URL construction.
#
# author: mjhwa@yahoo.com
##
def get_url(vin, command):
  return (BASE_PROXY_URL
          + '/api/1/vehicles/'
          + vin 
          + '/command/'
          + command)


def send_get(url):
  return send_request('GET', url, ACCESS_TOKEN, None, CERT)


def send_post(url, payload):
  return send_request('POST', url, ACCESS_TOKEN, payload, CERT)


##
# Loops through all vehicle data and prints to screen.  
#
# author: mjhwa@yahoo.come
##
def print_all_vehicle_data(vin):
  data = get_vehicle_data(vin)

  if ('error' in data):
    raise Exception (data['error'])

  print_json(data, 0)


def main(parser):
  args = parser.parse_args()

  if (args.print):
    print_all_vehicle_data(args.print[0])
  elif (args.schedule_software_update):
    if args.schedule_software_update[0] == 'm3':
      schedule_software_update(M3_VIN, 0)
    elif args.schedule_software_update[0] == 'mx':
      schedule_software_update(MX_VIN, 0)
    else:
      parser.error('invalid VEHICLE type, must be \'m3\' or \'mx\'')
  else:
    parser.print_help()


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
                    prog='api.py',
                    description='API calls for Tesla Vehicles (Pre-2021 Model X and S).',
                    formatter_class=CustomHelpFormatter)
  group = parser.add_mutually_exclusive_group()
  group.add_argument(
                     '-p', 
                     '--print', 
                     help='prints all the vehicle data; VIN is the Vehicle Identification Number you can find on the '
                          'car or in the mobile app',
                     nargs=1,
                     metavar='VIN'
                    )
  group.add_argument(
                     '-s', 
                     '--schedule_software_update', 
                     help='mimics scheduling a software update from the vehicle interface; VEHICLE can be \'m3\' or '
                          '\'mx\'',
                     nargs=1,
                     metavar='VEHICLE'
                    )

  main(parser)