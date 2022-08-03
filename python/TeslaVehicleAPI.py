import requests
import json
import time

from Logger import logError
from Utilities import printJson, getToken

ACCESS_TOKEN = getToken()['tesla']['access_token']

WAIT_TIME = 30 
URL = 'https://owner-api.teslamotors.com/api/1/vehicles'


##
# Retrieves the vehicle ID, which changes from time to time, by the VIN, which 
# doesn't change.  The vehicle ID is required for many of the API calls.
# 
# author: mjhwa@yahoo.com 
##
def getVehicleId(vin):
  try:
    response = json.loads(
      requests.get(
        URL, 
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
    url = (URL
           + '/'
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
# when it's asleep.
#
# author: mjhwa@yahoo.com
##
def wakeVehicle(vin):
  try:
    url = (URL
           + '/'
           + getVehicleId(vin) 
           + '/wake_up')

    requests.post(
      url, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
    )
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
    url = (URL
           + '/'
           + getVehicleId(vin) 
           + '/command/charge_start')

    requests.post(
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
    url = (URL
           + '/'
           + getVehicleId(vin)
           + '/command/charge_stop')

    requests.post(
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
    url = (URL
           + '/'
           + getVehicleId(vin) 
           + '/command/set_scheduled_charging')

    payload = {
      'enable': 'True',
      'time': time
    }

    requests.post(
      url, 
      data=payload, 
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
    url = (URL
           + '/'
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

    requests.post(
      url,
      data=payload,
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
    url = (URL
           + '/'
           + getVehicleId(vin)
           + '/command/set_charging_amps')

    payload = {
      'charging_amps': amps
    }

    requests.post(
      url,
      data=payload,
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
    url = (URL
           + '/'
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
    logError('setCarTemp(' + vin + '): ' + str(e))


##
# Function to set vehicle seat heater level.
#
# author: mjhwa@yahoo.com
##
def setCarSeatHeating(vin, seat, setting):
  try:
    url = (URL
           + '/'
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
    logError('setCarSeatHeating(' + vin + '): ' + str(e))


##
# Function to start vehicle preconditioning.
#
# author: mjhwa@yahoo.com
##
def preconditionCarStart(vin):
  try:  
    url = (URL
           + '/'
           + getVehicleId(vin) 
           + '/command/auto_conditioning_start')

    requests.post(
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
    url = (URL
           + '/'
           + getVehicleId(vin)
           + '/command/auto_conditioning_stop')

    requests.post(
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
