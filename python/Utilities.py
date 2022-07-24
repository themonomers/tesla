import requests
import math
import json
import datetime
import configparser
import os

from Crypto import decrypt
from Logger import logError
from crontab import CronTab
from io import StringIO

buffer = StringIO(
  decrypt(
    os.path.join(
      os.path.dirname(os.path.abspath(__file__)), 
      'config.rsa'
    )
  ).decode('utf-8')
)
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
BASE_WEATHER_URL = 'https://api.openweathermap.org/data/2.5'


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
# attributes.  Gets current weather conditions.
#
# author: mjhwa@yahoo.com
##
def getCurrentWeather(zipcode):
  try:
    url = (BASE_WEATHER_URL
           + '/weather'
           + '?zip=' + zipcode
           + '&APPID=' + OPENWEATHERMAP_KEY
           + '&units=metric')

    response = requests.get(url)

    return json.loads(response.text)
  except Exception as e:
    logError('getCurrentWeather(): ' + str(e))


##
# Uses a free weather service with API to look up data by latitude and
# longitude or other attributes.  Gets daily weather conditions for 
# today + 7 days, and hourly weather conditions for 48 hours.
#
# author: mjhwa@yahoo.com
##
def getDailyWeather(lat, lng):
  try:
    url = (BASE_WEATHER_URL
           + '/onecall'
           + '?lat=' + str(lat)
           + '&lon=' + str(lng)
           + '&APPID=' + OPENWEATHERMAP_KEY
           + '&exclude=current,minutely,alerts'
           + '&units=metric')

    response = requests.get(url)

    return json.loads(response.text)
  except Exception as e:
    logError('getDailyWeather(): ' + str(e))


##
# Formats a key/value pair with indentions for formatting and printing out
# with a temperature conversion from Celcius to Fahrenheit.
#
# author: mjhwa@yahoo.com
##
def outputFahrenheit(key, value, indent):
  return output(key, str((value * 9 / 5) + 32) + ' (F)', indent)


##
# Formats a key/value pair with indentions for formatting and printing out
# to a date and time format.
#
# author: mjhwa@yahoo.com
##
def outputDate(key, value, indent):
  return output(key, datetime.datetime.fromtimestamp(value), indent)


##
# Formats a key/value pair with indentions for formatting and printing out.
#
# author: mjhwa@yahoo.com
##
def output(key, value, indent):
  space = ''
  for i in range(0, indent):
    space += ' '
  return(space + key + ' = ' + str(value))


##
# Takes a JSON object and recursively prints out it's name/value pairs with
# indentation for each level.
#
# author: mjhwa@yahoo.com
##
def printJson(json_obj, level):
  offset = ''
  offset += '  ' * level

  if (isinstance(json_obj, dict) == True):
    for key in json_obj:

      value = json_obj[key]
      if ((isinstance(value, dict) == True) or (isinstance(value, list) == True)):
        print(offset + key)
        printJson(value, level + 1)
      else:
        print (offset + key + ' = ' + str(value))
  elif (isinstance(json_obj, list) == True):
    for x in json_obj:

      if (isinstance(x, list) == True):
        for key, value in x.iteritems():
          print(offset + key)
          printJson(value, level + 1)
      else:
        printJson(x, level)
  else:
    print (offset + str(json_obj))


def main():
  print('[1] getDistance')
  print('[2] getCurrentWeather')
  print('[3] getDailyWeather')

  try:
    choice = int(raw_input('selection: ')) # type: ignore
  except ValueError:
    return

  if (choice == 1):
    lat = float(raw_input('latitude: ')) # type: ignore
    lng = float(raw_input('longitude: ')) # type: ignore
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
    zip = raw_input('zip code: ') # type: ignore
    data = getCurrentWeather(zip)
    
    for key_1, value_1 in data.iteritems():
      if (isinstance(value_1, dict) == True):
        print(key_1)

        for key_2, value_2 in data[key_1].iteritems():
          if ((key_2 == 'sunrise') or (key_2 == 'sunset')):
            print(outputDate(key_2, value_2, 2))
          elif (
            (key_2 == 'temp')
            or (key_2 == 'temp_max')
            or (key_2 == 'temp_min')
            or (key_2 == 'feels_like')
          ):
            print(outputFahrenheit(key_2, value_2, 2))
          else:
            print(output(key_2, value_2, 2))
      elif (isinstance(value_1, list) == True):
        print(key_1)

        for index in range(len(data[key_1])):
          for key_2, value_2 in data[key_1][index].iteritems():
            print(output(key_2, value_2, 2))
      elif (key_1 == 'dt'):
        print(outputDate(key_1, value_1, 0))
      else:
        print(output(key_1, value_1, 0))
  elif (choice == 3):
    data = getDailyWeather(HOME_LAT, HOME_LNG)

    for key_1, value_1 in data.iteritems():
      if (isinstance(value_1, dict) == True):
        print(key_1)
      elif (isinstance(value_1, list) == True):
        print(key_1)

        for index in range(len(data[key_1])):
          print(str(index) + '.')

          for key_2, value_2 in data[key_1][index].iteritems():
            if (isinstance(value_2, list) == True):
              print(output(key_2, '', 2))

              for index_2 in range(len(data[key_1][index][key_2])):

                for key_3, value_3 in data[key_1][index][key_2][index_2].iteritems():
                  print(output(key_3, value_3, 4))
            elif (isinstance(value_2, dict) == True):
              print(output(key_2, '', 2))

              for key_3, value_3 in data[key_1][index][key_2].iteritems():
                if ((key_3 == 'min') 
                    or (key_3 == 'max')
                    or (key_3 == 'eve')
                    or (key_3 == 'morn')
                    or (key_3 == 'night')
                    or (key_3 == 'day')):
                  print(outputFahrenheit(key_3, value_3, 4))
                else:
                  print(output(key_3, value_3, 4))
            elif ((key_2 == 'sunrise') 
                  or (key_2 == 'sunset')
                  or (key_2 == 'moonrise')
                  or (key_2 == 'moonset')
                  or (key_2 == 'dt')):
              print(outputDate(key_2, value_2, 2))
            else:
              print(output(key_2, value_2, 2))
      else:
        print(output(key_1, value_1, 0))


if __name__ == "__main__":
  main()
