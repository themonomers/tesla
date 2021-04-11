import requests
import json
import time
import configparser

from Logger import logError

WAIT_TIME = 30 

config = configparser.ConfigParser()
config.sections()
config.read('config.ini')
ACCESS_TOKEN = config['tesla']['access_token']


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
# when it's asleep.
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
    url = ('https://owner-api.teslamotors.com/api/1/vehicles/' 
           + getVehicleId(vin) 
           + '/command/charge_start')

    requests.post(
      url, 
      headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
    )
  except Exception as e:
    logError('chargeVehicle(' + vin + '): ' + str(e))


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
    logError('setCarTemp(' + vin + '): ' + str(e))


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
    logError('setCarSeatHeating(' + vin + '): ' + str(e))


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
    logError('preconditionCarStart(' + vin + '): ' + str(e))


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
    logError('preconditionCarStop(' + vin + '): ' + str(e))

##
# Loops through all vehicle data and prints to screen.  There are some additional
# nested objects that aren't printed out to their own separate lines yet.
#
# author: mjhwa@yahoo.come
##
def printAllVehicleData(vin):
  try:
    data = getVehicleData(vin)

    for key, value in data['response'].iteritems():
      if key == 'charge_state':
        print(key)

        for key, value in data['response']['charge_state'].iteritems():
          print('  ' + key + ' = ' + str(value))
      elif key == 'climate_state':
        print(key)

        for key, value in data['response']['climate_state'].iteritems():
          print('  ' + key + ' = ' + str(value))
      elif key == 'vehicle_state':
        print(key)

        for key, value in data['response']['vehicle_state'].iteritems():
          print('  ' + key + ' = ' + str(value))
      elif key == 'drive_state':
        print(key)

        for key, value in data['response']['drive_state'].iteritems():
          print('  ' + key + ' = ' + str(value))
      elif key == 'gui_settings':
        print(key)

        for key, value in data['response']['gui_settings'].iteritems():
          print('  ' + key + ' = ' + str(value))
      elif key == 'vehicle_config':
        print(key)

        for key, value in data['response']['vehicle_config'].iteritems():
          print('  ' + key + ' = ' + str(value))
      else:
        print(key + ' = ' + str(value))
  except Exception as e:
    logError('printAllVehicleData( ' + vin + '): ' + str(e))
    wakeVehicle(vin)
    printAllVehicleData(vin)


def main():
  vin = raw_input('printAllVehicleData VIN: ')
  printAllVehicleData(vin)

if __name__ == "__main__":
  main()
