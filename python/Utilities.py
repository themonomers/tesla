import requests
import math
import json
import datetime
import configparser

from Crypto import decrypt
from Logger import logError
from crontab import CronTab
from io import StringIO

buffer = StringIO(decrypt('config.rsa').decode('utf-8'))
config = configparser.ConfigParser()
config.sections()
config.readfp(buffer)
HOME_LAT = float(config['vehicle']['home_lat'])
HOME_LNG = float(config['vehicle']['home_lng'])
NAPA_LAT = float(config['vehicle']['napa_lat'])
NAPA_LNG = float(config['vehicle']['napa_lng'])
OPENWEATHERMAP_KEY = config['weather']['openweathermap_key']
buffer.close()

R = 3958.8  #Earth radius in miles


##
# Removes crontab for a single command.
#
# author: mjhwa@yahoo.com
##
def deleteCronTab(command):
  try: 
    cron = CronTab(user='pi')
    job = cron.find_command(command)
    cron.remove(job)
    cron.write()
  except Exception as e:
    logError('deleteCronTab(' + command + '): ' + str(e))


##
# Creates crontab entry for a single command.
#
# author: mjhwa@yahoo.com
##
def createCronTab(command, month, day, hour, minute):
  try:
    cron = CronTab(user='pi')
    job = cron.new(command=command)
    job.month.on(month)
    job.day.on(day)
    job.hour.on(hour)
    job.minute.on(minute)
    cron.write()
  except Exception as e:
    logError('createCronTab(' + command + '): ' + str(e))


##
# Calculates if the distance of the car is greater than 0.25 miles away from 
# home.  The calculation uses Haversine Formula expressed in terms of a 
# two-argument inverse tangent function to calculate the great circle distance 
# between two points on the Earth. This is the method recommended for 
# calculating short distances by Bob Chamberlain (rgc@jpl.nasa.gov) of Caltech 
# and NASA's Jet Propulsion Laboratory as described on the U.S. Census Bureau 
# Web site.
#
# author: mjhwa@yahoo.com
##
def isVehicleAtHome(data):
  return isVehicleAtLocation(data, HOME_LAT, HOME_LNG)


def isVehicleAtNapa(data):
  return isVehicleAtLocation(data, NAPA_LAT, NAPA_LNG)


def isVehicleAtLocation(data, lat, lng):
  try:
    d = getDistance(data['response']['drive_state']['latitude'], 
                    data['response']['drive_state']['longitude'], 
                    lat, lng)
  
    # check if the car is more than a quarter of a mile away 
    if (d < 0.25):
      return True
    else:
      return False
  except Exception as e:
    logError('isVehicleAtLocation(): ' + str(e))


def getDistance(car_lat, car_lng, x_lat, x_lng):
  diff_lat = toRad(car_lat - x_lat)
  diff_lng = toRad(car_lng - x_lng)  
  
  a = ((math.sin(diff_lat/2) * math.sin(diff_lat/2)) 
        + math.cos(x_lat) 
        * math.cos(car_lat) 
        * (math.sin(diff_lng/2) * math.sin(diff_lng/2)))
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
  d = R * c
  
  return d


def toRad(x):
  return x * math.pi/180


##
# Uses a free weather service with API to look up data by zipcode or other 
# attributes.
#
# author: mjhwa@yahoo.com
##
def getWeather(zipcode):
  try:
    url = ('https://api.openweathermap.org/data/2.5/weather'
           + '?zip=' + zipcode
           + '&APPID=' + OPENWEATHERMAP_KEY
           + '&units=metric')

    response = requests.get(url)

    return json.loads(response.text)
  except Exception as e:
    logError('getWeather(): ' + str(e))


def main():
  print('[1] getDistance')
  print('[2] getWeather')
  try:
    choice = int(raw_input('selection: '))
  except ValueError:
    return

  if (choice == 1):
    lat = float(raw_input('latitude: '))
    lng = float(raw_input('longitude: '))
    print(
      'distance from home: ' 
      + str(
        getDistance(
          lat, 
          lng, 
          HOME_LAT,
          HOME_LNG
        )
      )
    )
  elif (choice == 2):
    zip = raw_input('zip code: ')
    data = getWeather(zip)
    
    for key, value in data.iteritems():
      if (key == 'sys'):
        print(key)

        for key, value in data['sys'].iteritems():
          if ((key == 'sunrise') or (key == 'sunset')):
            print(
              '  ' 
              + key 
              + ' = ' 
              + str(
                datetime.datetime.fromtimestamp(value)
              )
            )
          else:
            print('  ' + key + ' = ' + str(value))
      elif (key == 'weather'):
        print(key)
       
        for key, value in data['weather'][0].iteritems():
          print('  ' + key + ' = ' + str(value))
      elif (key == 'coord'):
        print(key)
       
        for key, value in data['coord'].iteritems():
          print('  ' + key + ' = ' + str(value))
      elif (key == 'dt'):
        print(
          key
          + ' = '
          + str(
            datetime.datetime.fromtimestamp(value)
          )
        )
      elif (key == 'main'):
        print(key)
       
        for key, value in data['main'].iteritems():
          if (
            (key == 'temp')
            or (key == 'temp_max')
            or (key == 'temp_min')
            or (key == 'feels_like')
          ):
            print('  ' + key + '(F) = ' + str((value * 9 / 5) + 32))
          else: 
            print('  ' + key + ' = ' + str(value))
      elif (key == 'wind'):
        print(key)
       
        for key, value in data['wind'].iteritems():
          print('  ' + key + ' = ' + str(value))
      else:
        print(key + ' = ' + str(value))

if __name__ == "__main__":
  main()
