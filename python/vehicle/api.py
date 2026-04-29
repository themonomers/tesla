import requests
import vehicle.commandproxy as commandproxy

from common.utilities import print_json, get_token, get_config
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
def start_charge_vehicle(vin):
  try:
    if vin == M3_VIN:
      return commandproxy.start_charge_vehicle(vin)
    
    url = (BASE_OWNER_URL
           + '/vehicles/'
           + get_vehicle_id(vin) 
           + '/command/charge_start')

    return requests.post(
      url, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
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
    if vin == M3_VIN:
      return commandproxy.stop_charge_vehicle(vin)
  
    url = (BASE_OWNER_URL
           + '/vehicles/'
           + get_vehicle_id(vin)
           + '/command/charge_stop')

    return requests.post(
      url,
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
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
    if vin == M3_VIN:
      return commandproxy.set_scheduled_charging(vin, time)

    url = (BASE_OWNER_URL
           + '/vehicles/'
           + get_vehicle_id(vin) 
           + '/command/set_scheduled_charging')

    payload = {
      'enable': 'True',
      'time': time
    }

    return requests.post(
      url, 
      json=payload, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
    )
  except Exception as e:
    log_error('set_scheduled_charging(' + vin + '):', e)


##
# Per Tesla (https://developer.tesla.com/docs/fleet-api/endpoints/vehicle-commands#set-scheduled-departure):  
# This endpoint is not recommended beginning with firmware version 2024.26.
#
# Sends command and parameters to set a specific vehicle to charge and/or
# precondition by a departure time.  Departure Time and Off-Peak Charge End 
# Time are in minutes, e.g. 7:30 AM = (7 * 60) + 30 = 450
#
# author: mjhwa@yahoo.com
##
def set_scheduled_departure(
  vin, 
  depart_time, 
  precondition_enable, 
  precondition_weekdays, 
  off_peak_charging_enable, 
  off_peak_weekdays, 
  off_peak_end_time
):
  try:
    url = (BASE_OWNER_URL
           + '/vehicles/'
           + get_vehicle_id(vin)
           + '/command/set_scheduled_departure')

    payload = {
      'enable': 'True',
      'departure_time': depart_time,
      'preconditioning_enabled': precondition_enable,
      'preconditioning_weekdays_only': precondition_weekdays,
      'off_peak_charging_enabled': off_peak_charging_enable,
      'off_peak_charging_weekdays_only': off_peak_weekdays,
      'end_off_peak_time': off_peak_end_time
    }

    return requests.post(
      url,
      json=payload,
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
    )
  except Exception as e:
    log_error('set_scheduled_departure(' + vin + '):', e)


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
# Function to set vehicle temperature.
#
# author: mjhwa@yahoo.com
##
def set_car_temp(vin, d_temp, p_temp):
  try:
    if vin == M3_VIN:
      return commandproxy.set_car_temp(vin, d_temp, p_temp)

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
    log_error('set_car_temp(' + vin + '):', e)


##
# Function to set vehicle seat heater level.
#
# author: mjhwa@yahoo.com
##
def set_car_seat_heating(vin, seat, setting):
  try:
    if vin == M3_VIN:
      return commandproxy.set_car_seat_heating(vin, seat, setting)

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
    log_error('set_car_seat_heating(' + vin + '):', e)


##
# Function to set vehicle seat cooler level.
#
# author: mjhwa@yahoo.com
##
def set_car_seat_cooling(vin, seat, setting):
  try:
    return commandproxy.set_car_seat_cooling(vin, seat, setting)
  except Exception as e:
    log_error('set_car_seat_cooling(' + vin + '):', e)


##
# Function to start vehicle preconditioning.
#
# author: mjhwa@yahoo.com
##
def precondition_car_start(vin):
  try:  
    if vin == M3_VIN:
      return commandproxy.precondition_car_start(vin)

    url = (BASE_OWNER_URL
           + '/vehicles/'
           + get_vehicle_id(vin) 
           + '/command/auto_conditioning_start')

    return requests.post(
      url, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
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
    if vin == M3_VIN:
      return commandproxy.precondition_car_stop(vin)

    url = (BASE_OWNER_URL
           + '/vehicles/'
           + get_vehicle_id(vin)
           + '/command/auto_conditioning_stop')

    return requests.post(
      url, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
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
