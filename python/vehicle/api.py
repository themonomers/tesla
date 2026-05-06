import requests
import argparse
import vehicle.commandproxy as commandproxy

from common.utilities import print_json, get_token, get_config, CustomHelpFormatter
from common.logger import log_error

ACCESS_TOKEN = get_token()['tesla']['access_token']
config = get_config()
M3_VIN = config['vehicle']['m3_vin']
MX_VIN = config['vehicle']['mx_vin']
BASE_OWNER_URL = config['tesla']['base_owner_url']


##
# Retrieves the vehicle ID, which changes from time to time, by the VIN, which 
# doesn't change.  The vehicle ID is required for many of the API calls.
# 
# author: mjhwa@yahoo.com 
##
def get_vehicle_id(vin):
  try:
    if vin == M3_VIN:
      data = commandproxy.get_vehicle_data(M3_VIN)

    if vin == MX_VIN:
      data = commandproxy.get_vehicle_data(MX_VIN)

    return data['response']['id_s']
  except Exception as e:
    log_error('get_vehicle_id(' + vin + '):', e)


##
# Retrieves the vehicle data needed for higher level functions to drive 
# calcuations and actions.
# 
# author: mjhwa@yahoo.com 
##
def get_vehicle_data(vin):
  try:
    return commandproxy.get_vehicle_data(vin)
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
    return commandproxy.wake_vehicle(vin)
  except Exception as e:
    log_error('wake_vehicle(' + vin + '):', e)


##
# Function to send API call to start charging a vehicle.
#
# author: mjhwa@yahoo.com
##
def start_charge(vin):
  try:
    if vin == M3_VIN:
      return commandproxy.start_charge(vin)
    
    url = (BASE_OWNER_URL
           + '/vehicles/'
           + get_vehicle_id(vin) 
           + '/command/charge_start')

    return requests.post(
      url, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
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
    if vin == M3_VIN:
      return commandproxy.stop_charge(vin)
  
    url = (BASE_OWNER_URL
           + '/vehicles/'
           + get_vehicle_id(vin)
           + '/command/charge_stop')

    return requests.post(
      url,
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
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
    if vin == M3_VIN:
      return commandproxy.add_charge_schedule(vin, lat, lon, start_time, id)

    url = (BASE_OWNER_URL
           + '/vehicles/'
           + get_vehicle_id(vin) 
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

    return requests.post(
      url, 
      json=payload, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
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
    if vin == M3_VIN:
      return commandproxy.remove_charge_schedule(vin, id)
    
    url = (BASE_OWNER_URL
           + '/vehicles/'
           + get_vehicle_id(vin) 
           + '/command/remove_charge_schedule')

    payload = {
      'id': id
    }

    return requests.post(
      url, 
      json=payload, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
    )
  except Exception as e:
    log_error('remove_charge_schedule(' + vin + '):', e)
  

##
# Sends command to set the charging amps for a specified vehicle.
#
# author: mjhwa@yahoo.com
##
def set_charging_amps(vin, amps):
  try:
    url = (BASE_OWNER_URL
           + '/vehicles/'
           + get_vehicle_id(vin)
           + '/command/set_charging_amps')

    payload = {
      'charging_amps': amps
    }

    return requests.post(
      url,
      json=payload,
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
    )
  except Exception as e:
    log_error('set_charging_amps(' + vin + '):', e)


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
    if vin == M3_VIN:
      return commandproxy.set_temp(vin, d_temp, p_temp)

    url = (BASE_OWNER_URL
           + '/vehicles/'
           + get_vehicle_id(vin) 
           + '/command/set_temps')

    payload = {
      'driver_temp': d_temp,
      'passenger_temp': p_temp
    }

    return requests.post(
      url, 
      json=payload, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
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
    if vin == M3_VIN:
      return commandproxy.set_seat_heating(vin, seat, setting)

    url = (BASE_OWNER_URL
           + '/vehicles/'
           + get_vehicle_id(vin) 
           + '/command/remote_seat_heater_request')

    payload = {
      'heater': seat,
      'level': setting
    }
#    "payload": JSON.stringify({'heater': '0', 'level': seats[0],
#                               'heater': '1', 'level': seats[1],
#                               'heater': '2', 'level': seats[2],
#                               'heater': '4', 'level': seats[3],
#                               'heater': '5', 'level': seats[4]})

    return requests.post(
      url, 
      json=payload, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
    )
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
    return commandproxy.set_seat_cooling(vin, seat, setting)
  except Exception as e:
    log_error('set_seat_cooling(' + vin + '):', e)


##
# Function to start vehicle preconditioning.
#
# author: mjhwa@yahoo.com
##
def start_precondition(vin):
  try:  
    if vin == M3_VIN:
      return commandproxy.start_precondition(vin)

    url = (BASE_OWNER_URL
           + '/vehicles/'
           + get_vehicle_id(vin) 
           + '/command/auto_conditioning_start')

    return requests.post(
      url, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
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
    if vin == M3_VIN:
      return commandproxy.stop_precondition(vin)

    url = (BASE_OWNER_URL
           + '/vehicles/'
           + get_vehicle_id(vin)
           + '/command/auto_conditioning_stop')

    return requests.post(
      url, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
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
    if vin == M3_VIN:
      return commandproxy.schedule_software_update(vin, time)

    url = (BASE_OWNER_URL
           + '/vehicles/'
           + get_vehicle_id(vin)
           + '/command/schedule_software_update')

    payload = {
      'offset_sec': time
    }

    return requests.post(
      url,
      json=payload,
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
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