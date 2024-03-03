import requests
import json
import time
import urllib.parse
import urllib3

from Logger import logError
from Utilities import printJson, getToken, getConfig

ACCESS_TOKEN = getToken()['tesla']['access_token']
config = getConfig()
BASE_PROXY_URL = config['tesla']['base_proxy_url']
CERT = config['tesla']['certificate']

WAIT_TIME = 30 


##
# Retrieves the vehicle data needed for higher level functions to drive 
# calcuations and actions.
# 
# author: mjhwa@yahoo.com 
##
def getVehicleData(vin):
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
               + 'closures_state;'
               + 'drive_state'))

    urllib3.disable_warnings(urllib3.exceptions.SubjectAltNameWarning)

    response = requests.get(
      url, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN},
      verify=CERT
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
    logError('wakeVehicle(' + vin + '): ' + str(e))
    time.sleep(WAIT_TIME)
    wakeVehicle(vin)


##
# Function to send API call to stop charging a vehicle.
#
# author: mjhwa@yahoo.com
##
def stopChargeVehicle(vin):
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
    logError('setScheduledCharging(' + vin + '): ' + str(e))


##
# Function to set vehicle temperature.
#
# author: mjhwa@yahoo.com
##
def setCarTemp(vin, d_temp, p_temp):
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
    logError('setCarTemp(' + vin + '): ' + str(e))


##
# Function to set vehicle seat heater level.
#
# author: mjhwa@yahoo.com
##
def setCarSeatHeating(vin, seat, setting):
  try:
    url = (BASE_PROXY_URL
           + '/vehicles/'
           + vin 
           + '/command/remote_seat_heater_request')

    payload = {
      'seat_position': seat,
      'level': setting
    }
#    "payload": JSON.stringify({'heater': '0', 'level': seats[0],
#                               'heater': '1', 'level': seats[1],
#                               'heater': '2', 'level': seats[2],
#                               'heater': '4', 'level': seats[3],
#                               'heater': '5', 'level': seats[4]})

    urllib3.disable_warnings(urllib3.exceptions.SubjectAltNameWarning)

    return requests.post(
      url, 
      json=payload, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN},
      verify=CERT
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
    logError('preconditionCarStart(' + vin + '): ' + str(e))


##
# Function to stop vehicle preconditioning.
#
# author: mjhwa@yahoo.com
##
def preconditionCarStop(vin):
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
