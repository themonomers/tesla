import json
import time
import urllib.parse
import argparse

from common.utilities import (
  log,
  print_json, 
  get_config, 
  send_request, 
  CustomHelpFormatter
)
from common.tokenutil import get_token

ACCESS_TOKEN = get_token()['tesla']['access_token']

config = get_config()
M3_VIN = config['vehicle']['m3_vin']
MX_VIN = config['vehicle']['mx_vin']
BASE_OWNER_URL = config['tesla']['base_owner_url']
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

    response = send_get(url, CERT)

    if response.status_code != 200:
      wake_vehicle(vin)
      time.sleep(WAIT_TIME)
      return get_vehicle_data(vin)

    return json.loads(response.text)
  except Exception as e:
    log().error('get_vehicle_data(' + vin + '): ' + str(e))


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

    return send_post(url, None, CERT)
  except Exception as e:
    log().error('wake_vehicle(' + vin + '): ' + str(e))


##
# Function to send API call to start charging a vehicle.
#
# author: mjhwa@yahoo.com
##
def start_charge(vin):
  try:
    if vin == MX_VIN:
      return send_post(get_url(BASE_OWNER_URL, vin, 'charge_start'), None, None)

    return send_post(get_url(BASE_PROXY_URL, vin, 'charge_start'), None, CERT)
  except Exception as e:
    log().error('start_charge(' + vin + '): ' + str(e))


##
# Function to send API call to stop charging a vehicle.
#
# author: mjhwa@yahoo.com
##
def stop_charge(vin):
  try:
    if vin == MX_VIN:
      return send_post(get_url(BASE_OWNER_URL, vin, 'charge_stop'), None, None)
  
    return send_post(get_url(BASE_PROXY_URL, vin, 'charge_stop'), None, CERT)
  except Exception as e:
    log().error('stop_charge(' + vin + '): ' + str(e))


##
# Uses new endpoint to add a schedule for vehicle charging. 
# Scheduled Time is in minutes, e.g. 7:30 AM = 
# (7 * 60) + 30 = 450
#
# author: mjhwa@yahoo.com
##
def add_charge_schedule(vin, lat, lon, start_time, id):
  try:
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

    if vin == MX_VIN:
      return send_post(get_url(BASE_OWNER_URL, vin, 'add_charge_schedule'), payload, None)

    return send_post(get_url(BASE_PROXY_URL, vin, 'add_charge_schedule'), payload, CERT)
  except Exception as e:
    log().error('add_charge_schedule(' + vin + '): ' + str(e))


##
# Uses new endpoint to remove a schedule for vehicle charging. 
#
# author: mjhwa@yahoo.com
##
def remove_charge_schedule(vin, id):
  try:
    payload = {
      'id': id
    }

    if vin == MX_VIN:
      return send_post(get_url(BASE_OWNER_URL, vin, 'remove_charge_schedule'), payload, None)

    return send_post(get_url(BASE_PROXY_URL, vin, 'remove_charge_schedule'), payload, CERT)
  except Exception as e:
    log().error('remove_charge_schedule(' + vin + '): ' + str(e))
  

##
# Sends command to set the charging amps for a specified vehicle.
#
# author: mjhwa@yahoo.com
##
def set_charging_amps(vin, amps):
  try:
    payload = {
      'charging_amps': amps
    }

    if vin == MX_VIN:
      return send_post(get_url(BASE_OWNER_URL, vin, 'set_charging_amps'), payload, None)

    return send_post(get_url(BASE_PROXY_URL, vin, 'set_charging_amps'), payload, None)
  except Exception as e:
    log().error('set_charging_amps(' + vin + '): ' + str(e))


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
    payload = {
      'driver_temp': d_temp,
      'passenger_temp': p_temp
    }

    if vin == MX_VIN:
      return send_post(get_url(BASE_OWNER_URL, vin, 'set_temps'), payload, None)

    return send_post(get_url(BASE_PROXY_URL, vin, 'set_temps'), payload, CERT)
  except Exception as e:
    log().error('set_temp(' + vin + '): ' + str(e))


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
    if vin == MX_VIN:
      payload = {
        'heater': seat,
        'level': setting
      }
      return send_post(get_url(BASE_OWNER_URL, vin, 'remote_seat_heater_request'), payload, None)

    payload = {
      'seat_position': seat,
      'level': setting
    }
    return send_post(get_url(BASE_PROXY_URL, vin, 'remote_seat_heater_request'), payload, CERT)
  except Exception as e:
    log().error('set_seat_heating(' + vin + '): ' + str(e))


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
    payload = {
      'seat_position': seat,
      'seat_cooler_level': setting
    }

    return send_post(get_url(BASE_PROXY_URL, vin, 'remote_seat_cooler_request'), payload, CERT)
  except Exception as e:
    log().error('set_seat_cooling(' + vin + '): ' + str(e))


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
    payload = {
      'auto_climate_on': enable,
      'auto_seat_position': seat
    }

    return send_post(get_url(BASE_PROXY_URL, vin, 'remote_auto_seat_climate_request'), payload, CERT)
  except Exception as e:
    log().error('set_seat_climate_auto(' + vin + '): ' + str(e))


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
    payload = {
      'on': enable
    }

    return send_post(get_url(BASE_PROXY_URL, vin, 'remote_steering_wheel_heater_request'), payload, CERT)
  except Exception as e:
    log().error('set_steering_wheel_heating(' + vin + '): ' + str(e))


##
# Function to start vehicle preconditioning.
#
# author: mjhwa@yahoo.com
##
def start_precondition(vin):
  try:  
    if vin == MX_VIN:
      return send_post(get_url(BASE_OWNER_URL, vin, 'auto_conditioning_start'), None, None)

    return send_post(get_url(BASE_PROXY_URL, vin, 'auto_conditioning_start'), None, CERT)
  except Exception as e:
    log().error('start_precondition(' + vin + '): ' + str(e))


##
# Function to stop vehicle preconditioning.
#
# author: mjhwa@yahoo.com
##
def stop_precondition(vin):
  try:
    if vin == MX_VIN:
      return send_post(get_url(BASE_OWNER_URL, vin, 'auto_conditioning_stop'), None, None)

    return send_post(get_url(BASE_PROXY_URL, vin, 'auto_conditioning_stop'), None, CERT)
  except Exception as e:
    log().error('stop_precondition(' + vin + '): ' + str(e))


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

    if vin == MX_VIN:
      return send_post(get_url(BASE_OWNER_URL, vin, 'schedule_software_update'), payload, None)

    response = send_post(get_url(BASE_PROXY_URL, vin, 'schedule_software_update'), payload, CERT)
    if response.status_code != 200:
      wake_vehicle(vin)
      time.sleep(WAIT_TIME)
      return schedule_software_update(vin, offset_sec)

    return response 
  except Exception as e:
    log().error('schedule_software_update(' + vin + '): ' + str(e))


##
# Retrieves the vehicle ID, which changes from time to time, by the VIN, which 
# doesn't change.  The vehicle ID is required for many of the API calls.
# 
# author: mjhwa@yahoo.com 
##
def get_vehicle_id(vin):
  try:
    data = get_vehicle_data(vin)

    return data['response']['id_s']
  except Exception as e:
    log().error('get_vehicle_id(' + vin + '): ' + str(e))


###
# Centralize repetitive URL construction.
#
# author: mjhwa@yahoo.com
##
def get_url(base, vin, command):
  try:
    url = ''
    if (base == BASE_OWNER_URL):
      url = (base
            + '/vehicles/'
            + get_vehicle_id(vin)
            + '/command/'
            + command)
    elif (base == BASE_PROXY_URL):
      url = (base
            + '/vehicles/'
            + vin 
            + '/command/'
            + command)
    
    return url
  except Exception as e:
    log().error('get_url(' + url + '): ' + str(e))


def send_get(url, cert):
  return send_request('GET', url, ACCESS_TOKEN, None, cert)


def send_post(url, payload, cert):
  return send_request('POST', url, ACCESS_TOKEN, payload, cert)


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
    log().error('print_all_vehicle_data(' + vin + '): ' + str(e))


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