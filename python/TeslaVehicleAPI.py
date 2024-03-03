import requests
import json
import time
import urllib.parse
import TeslaVehicleCommandProxy

from Logger import logError
from Utilities import printJson, getToken, getConfig

ACCESS_TOKEN = getToken()['tesla']['access_token']
config = getConfig()
M3_VIN = config['vehicle']['m3_vin']
MX_VIN = config['vehicle']['mx_vin']
BASE_OWNER_URL = config['tesla']['base_owner_url']

WAIT_TIME = 30 


##
# Retrieves the vehicle ID, which changes from time to time, by the VIN, which 
# doesn't change.  The vehicle ID is required for many of the API calls.
# 
# author: mjhwa@yahoo.com 
##
def getVehicleId(vin):
  try:
    if vin == M3_VIN:
      data = TeslaVehicleCommandProxy.getVehicleData(M3_VIN)

    if vin == MX_VIN:
      data = TeslaVehicleCommandProxy.getVehicleData(MX_VIN)

    return data['response']['id_s']
  except Exception as e:
    logError('getVehicleId(' + vin + '): ' + str(e))


##
# Retrieves the vehicle data needed for higher level functions to drive 
# calcuations and actions.
# 
# author: mjhwa@yahoo.com 
##
def getVehicleData(vin):
  try:
    if vin == M3_VIN:
      return TeslaVehicleCommandProxy.getVehicleData(vin)

    url = (BASE_OWNER_URL
           + '/vehicles/'
           + getVehicleId(vin) 
           + '/vehicle_data?endpoints='
           + urllib.parse.quote(
               'location_data;'
               + 'charge_state;'
               + 'climate_state;'
               + 'vehicle_state;'
               + 'gui_settings;'
               + 'vehicle_config;'
               + 'closures_state;'
               + 'drive_state'))

    response = requests.get(
      url, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
    )

    return json.loads(response.text)
  except Exception as e:
    logError('getVehicleData(' + vin + '): ' + str(e))


##
# Function to repeatedly run (after a certain wait time) to wake the vehicle up
# when it's asleep.
#
# author: mjhwa@yahoo.com
##
def wakeVehicle(vin):
  try:
    return TeslaVehicleCommandProxy.wakeVehicle(vin)
  except Exception as e:
    logError('wakeVehicle(' + vin + '): ' + str(e))
    time.sleep(WAIT_TIME)
    wakeVehicle(vin)


##
# Function to send API call to start charging a vehicle.
#
# author: mjhwa@yahoo.com
##
def chargeVehicle(vin):
  try:
    url = (BASE_OWNER_URL
           + '/vehicles/'
           + getVehicleId(vin) 
           + '/command/charge_start')

    return requests.post(
      url, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
    )
  except Exception as e:
    logError('chargeVehicle(' + vin + '): ' + str(e))


##
# Function to send API call to stop charging a vehicle.
#
# author: mjhwa@yahoo.com
##
def stopChargeVehicle(vin):
  try:
    if vin == M3_VIN:
      return TeslaVehicleCommandProxy.stopChargeVehicle(vin)
  
    url = (BASE_OWNER_URL
           + '/vehicles/'
           + getVehicleId(vin)
           + '/command/charge_stop')

    return requests.post(
      url,
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
    )
  except Exception as e:
    logError('stopChargeVehicle(' + vin + '): ' + str(e))


##
# Sends command and parameter to set a specific vehicle to charge
# at a scheduled time.  Scheduled Time is in minutes, e.g. 7:30 AM = 
# (7 * 60) + 30 = 450
#
# author: mjhwa@yahoo.com
##
def setScheduledCharging(vin, time):
  try:
    if vin == M3_VIN:
      return TeslaVehicleCommandProxy.setScheduledCharging(vin, time)

    url = (BASE_OWNER_URL
           + '/vehicles/'
           + getVehicleId(vin) 
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
    logError('setScheduledCharging(' + vin + '): ' + str(e))


##
# Sends command and parameters to set a specific vehicle to charge and/or
# precondition by a departure time.  Departure Time and Off-Peak Charge End 
# Time are in minutes, e.g. 7:30 AM = (7 * 60) + 30 = 450
#
# author: mjhwa@yahoo.com
##
def setScheduledDeparture(
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
           + getVehicleId(vin)
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
    logError('setScheduledDeparture(' + vin + '): ' + str(e))


##
# Sends command to set the charging amps for a specified vehicle.
#
# author: mjhwa@yahoo.com
##
def setChargingAmps(vin, amps):
  try:
    url = (BASE_OWNER_URL
           + '/vehicles/'
           + getVehicleId(vin)
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
    logError('setChargingAmps(' + vin + '): ' + str(e))


##
# Function to set vehicle temperature.
#
# author: mjhwa@yahoo.com
##
def setCarTemp(vin, d_temp, p_temp):
  try:
    if vin == M3_VIN:
      return TeslaVehicleCommandProxy.setCarTemp(vin, d_temp, p_temp)

    url = (BASE_OWNER_URL
           + '/vehicles/'
           + getVehicleId(vin) 
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
    logError('setCarTemp(' + vin + '): ' + str(e))


##
# Function to set vehicle seat heater level.
#
# author: mjhwa@yahoo.com
##
def setCarSeatHeating(vin, seat, setting):
  try:
    if vin == M3_VIN:
      return TeslaVehicleCommandProxy.setCarSeatHeating(vin, seat, setting)

    url = (BASE_OWNER_URL
           + '/vehicles/'
           + getVehicleId(vin) 
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
    logError('setCarSeatHeating(' + vin + '): ' + str(e))


##
# Function to start vehicle preconditioning.
#
# author: mjhwa@yahoo.com
##
def preconditionCarStart(vin):
  try:  
    if vin == M3_VIN:
      return TeslaVehicleCommandProxy.preconditionCarStart(vin)

    url = (BASE_OWNER_URL
           + '/vehicles/'
           + getVehicleId(vin) 
           + '/command/auto_conditioning_start')

    return requests.post(
      url, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
    )
  except Exception as e:
    logError('preconditionCarStart(' + vin + '): ' + str(e))


##
# Function to stop vehicle preconditioning.
#
# author: mjhwa@yahoo.com
##
def preconditionCarStop(vin):
  try:
    if vin == M3_VIN:
      return TeslaVehicleCommandProxy.preconditionCarStop(vin)

    url = (BASE_OWNER_URL
           + '/vehicles/'
           + getVehicleId(vin)
           + '/command/auto_conditioning_stop')

    return requests.post(
      url, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
    )
  except Exception as e:
    logError('preconditionCarStop(' + vin + '): ' + str(e))

##
# Loops through all vehicle data and prints to screen.  
#
# author: mjhwa@yahoo.come
##
def printAllVehicleData(vin):
  try:
    data = getVehicleData(vin)

    if ('error' in data):
      raise Exception (data['error'])

    printJson(data, 0)
  except Exception as e:
    logError('printAllVehicleData(' + vin + '): ' + str(e))
    wakeVehicle(vin)
    printAllVehicleData(vin)


def main():
  vin = input('printAllVehicleData VIN: ')
  printAllVehicleData(vin)


if __name__ == "__main__":
  main()
