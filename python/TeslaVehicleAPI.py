import requests
import json
import time
import configparser

from Logger import *

WAIT_TIME = 30 

config = configparser.ConfigParser()
config.sections()
config.read('config.ini')
ACCESS_TOKEN = config['vehicle']['access_token']


##
# Retrieves the vehicle ID, which changes from time to time, by the VIN, which 
# doesn't change.  The vehicle ID is required for many of the API calls.
# 
# author: mjhwa@yahoo.com 
##
def getVehicleId(vin):
  try:
    url = 'https://owner-api.teslamotors.com/api/1/vehicles'
    
    response = json.loads(
      requests.get(
        url, 
        headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
      ).text
    )
    for x in response['response']:
      if x['vin'] == vin:
        return x['id_s']
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
    url = ('https://owner-api.teslamotors.com/api/1/vehicles/'
           + getVehicleId(vin) 
           + '/vehicle_data')

    response = requests.get(
      url, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
    )
    return json.loads(response.text)
  except Exception as e:
    logError('getVehicleData(' + vin + '): ' + str(e))


##
# Function to repeatedly run (after a certain wait time) to wake the vehicle up
# when it's asleep. It will time out from the Google Apps Script trigger after
# 30s if it doesn't wake up.
#
# author: mjhwa@yahoo.com
##
def wakeVehicle(vin):
  try:
    url = ('https://owner-api.teslamotors.com/api/1/vehicles/' 
           + getVehicleId(vin) 
           + '/wake_up')

    requests.post(
      url, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
    )
  except Exception as e:
    logError('wakeVehicle(' + vin + '): ' + e)
    time.sleep(WAIT_TIME)
    wakeVehicle(vin)


##
# Function to send API call to start charging a vehicle.
#
# author: mjhwa@yahoo.com
##
def chargeVehicle(vin):
  try:
    url = ('https://owner-api.teslamotors.com/api/1/vehicles/' 
           + getVehicleId(vin) 
           + '/command/charge_start')

    requests.post(
      url, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
    )
  except Exception as e:
    logError('chargeVehicle(' + vin + '): ' + e)


##
# Function to set vehicle temperature.
#
# author: mjhwa@yahoo.com
##
def setCarTemp(vin, d_temp, p_temp):
  try:
    url = ('https://owner-api.teslamotors.com/api/1/vehicles/' 
           + getVehicleId(vin) 
           + '/command/set_temps')

    payload = {
      'driver_temp': d_temp,
      'passenger_temp': p_temp
    }

    requests.post(
      url, 
      data=payload, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
    )
  except Exception as e:
    logError('setCarTemp(' + vin + '): ' + e)


##
# Function to set vehicle seat heater level.
#
# author: mjhwa@yahoo.com
##
def setCarSeatHeating(vin, seat, setting):
  try:
    url = ('https://owner-api.teslamotors.com/api/1/vehicles/' 
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

    requests.post(
      url, 
      data=payload, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
    )
  except Exception as e:
    logError('setCarSeatHeating(' + vin + '): ' + e)


##
# Function to start vehicle preconditioning.
#
# author: mjhwa@yahoo.com
##
def preconditionCarStart(vin):
  try:  
    url = ('https://owner-api.teslamotors.com/api/1/vehicles/' 
           + getVehicleId(vin) 
           + '/command/auto_conditioning_start')

    requests.post(
      url, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
    )
  except Exception as e:
    logError('preconditionCarStart(' + vin + '): ' + e)


##
# Function to stop vehicle preconditioning.
#
# author: mjhwa@yahoo.com
##
def preconditionCarStop(vin):
  try:
    url = ('https://owner-api.teslamotors.com/api/1/vehicles/'
           + getVehicleId(vin)
           + '/command/auto_conditioning_stop')

    requests.post(
      url, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
    )
  except Exception as e:
    logError('preconditionCarStop(' + vin + '): ' + e)

