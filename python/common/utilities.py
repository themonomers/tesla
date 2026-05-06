import requests
import math
import json
import datetime
import zoneinfo
import configparser
import os
import time
import argparse

from common.crypto import decrypt
from crontab import CronTab
from datetime import datetime, timedelta
from io import StringIO

R = 3958.8  #Earth radius in miles
WAIT_TIME = 30  # seconds


##
# Retrieves dictionary of configuration values.
#
# author: mjhwa@yahoo.com
##
def get_config():
  try:
    buffer = StringIO(
      decrypt(
        os.path.join(
          os.path.dirname(os.path.abspath(__file__)),
          'config.xor'
        ),
        os.path.join(
          os.path.dirname(os.path.abspath(__file__)),
          'tesla_private_key.pem'
        )
      )
    )
    config = configparser.ConfigParser()
    config.sections()
    config.read_file(buffer)
    values = {s:dict(config.items(s)) for s in config.sections()}
    buffer.close()
    return values
  except Exception as e:
    logger.log_error_std_out('get_config():', e)

config = get_config()
PRIMARY_LAT = float(config['vehicle']['primary_lat'])
PRIMARY_LNG = float(config['vehicle']['primary_lng'])
SECONDARY_LAT = float(config['vehicle']['secondary_lat'])
SECONDARY_LNG = float(config['vehicle']['secondary_lng'])
OPENWEATHERMAP_KEY = config['weather']['openweathermap_key']
BASE_WEATHER_URL = config['weather']['base_url']
TIME_ZONE = config['general']['timezone']
PAC = zoneinfo.ZoneInfo(TIME_ZONE)


##
# Retrievies dictionary of access token values.
#
# author: mjhwa@yahoo.com
##
def get_token():
  try:
    buffer = StringIO(
      decrypt(
        os.path.join(
          os.path.dirname(os.path.abspath(__file__)),
          'token.xor'
        ),
        os.path.join(
          os.path.dirname(os.path.abspath(__file__)),
          'tesla_private_key.pem'
        )
      )
    )
    config = configparser.ConfigParser()
    config.sections()
    config.read_file(buffer)
    values = {s:dict(config.items(s)) for s in config.sections()}
    buffer.close()
    return values
  except Exception as e:
    logger.log_error('get_token():', e)


##
# Removes crontab for a single command.
#
# author: mjhwa@yahoo.com
##
def delete_cron_tab(command):
  try: 
    cron = CronTab(user='pi')
    job = cron.find_command(command)
    cron.remove(job)
    cron.write()
  except Exception as e:
    logger.log_error('delete_cron_tab():', e)


##
# Creates crontab entry for a single command.
#
# author: mjhwa@yahoo.com
##
def create_cron_tab(command, month, day, hour, minute):
  try:
    cron = CronTab(user='pi')
    job = cron.new(command=command)
    job.month.on(month)
    job.day.on(day)
    job.hour.on(hour)
    job.minute.on(minute)
    cron.write()
  except Exception as e:
    logger.log_error('create_cron_tab():', e)


##
# Calculates if the distance of the car is greater than 0.25 miles away from the
# primary location.  The calculation uses Haversine Formula expressed in terms of a 
# two-argument inverse tangent function to calculate the great circle distance 
# between two points on the Earth. This is the method recommended for 
# calculating short distances by Bob Chamberlain (rgc@jpl.nasa.gov) of Caltech 
# and NASA's Jet Propulsion Laboratory as described on the U.S. Census Bureau 
# Web site.
#
# author: mjhwa@yahoo.com
##
def is_vehicle_at_primary(data):
  return is_vehicle_at_location(data, PRIMARY_LAT, PRIMARY_LNG)


def is_vehicle_at_secondary(data):
  return is_vehicle_at_location(data, SECONDARY_LAT, SECONDARY_LNG)


def is_vehicle_at_location(data, lat, lng):
  try:
    d = get_distance(data['response']['drive_state']['latitude'], 
                     data['response']['drive_state']['longitude'], 
                     lat, lng)
  
    # check if the car is more than a quarter of a mile away 
    if (d < 0.25):
      return True
    else:
      return False
  except Exception as e:
    logger.log_warn('is_vehicle_at_location():' + str(e))
    return False


def get_distance(car_lat, car_lng, x_lat, x_lng):
  try:
    diff_lat = to_rad(car_lat - x_lat)
    diff_lng = to_rad(car_lng - x_lng)  
    
    a = ((math.sin(diff_lat/2) * math.sin(diff_lat/2)) 
          + math.cos(x_lat) 
          * math.cos(car_lat) 
          * (math.sin(diff_lng/2) * math.sin(diff_lng/2)))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R * c
    
    return d
  except Exception as e:
    logger.log_error('get_distance():', e)


def to_rad(x):
  return x * math.pi/180


##
# Helps format the charging or preconditioning time by defaulting the date.
#
# author: mjhwa@yahoo.com
##
def get_tomorrow_time(time):
  try:
    return datetime.strptime(
        str((datetime.now() + timedelta(1)).replace(tzinfo=PAC).year)
      + '-'
      + str((datetime.now() + timedelta(1)).replace(tzinfo=PAC).month)
      + '-'
      + str((datetime.now() + timedelta(1)).replace(tzinfo=PAC).day)
      + 'T'
      + time, '%Y-%m-%dT%H:%M'
    ).replace(tzinfo=PAC)
  except Exception as e:
    logger.log_error('get_tomorrow_time():', e)


def get_today_time(time):
  try:
    return datetime.strptime(
        str(datetime.now().replace(tzinfo=PAC).year)
      + '-'
      + str(datetime.now().replace(tzinfo=PAC).month)
      + '-'
      + str(datetime.now().replace(tzinfo=PAC).day)
      + 'T'
      + time, '%Y-%m-%dT%H:%M'
    ).replace(tzinfo=PAC)
  except Exception as e:
    logger.log_error('get_today_time():', e)


##
# Uses a free weather service with API to look up data by zipcode or other 
# attributes.  Gets current weather conditions.
#
# author: mjhwa@yahoo.com
##
def get_current_weather(lat, lng):
  try:
    url = (BASE_WEATHER_URL
           + '/onecall'
           + '?lat=' + str(lat)
           + '&lon=' + str(lng)
           + '&appid=' + OPENWEATHERMAP_KEY
           + '&exclude=minutely,hourly,daily,alerts'
           + '&units=metric')

    response = requests.get(url)

    if (response.status_code != 200):
      time.sleep(WAIT_TIME)
      return get_current_weather(lat, lng)

    return json.loads(response.text)
  except Exception as e:
    logger.log_error('get_current_weather():', e)
    

##
# Uses a free weather service with API to look up data by latitude and
# longitude or other attributes.  Gets daily weather conditions for 
# today + 7 days, and hourly weather conditions for 48 hours.
#
# author: mjhwa@yahoo.com
##
def get_daily_weather(lat, lng):
  try:
    url = (BASE_WEATHER_URL
           + '/onecall'
           + '?lat=' + str(lat)
           + '&lon=' + str(lng)
           + '&appid=' + OPENWEATHERMAP_KEY
           + '&exclude=current,minutely,alerts'
           + '&units=metric')

    response = requests.get(url)

    if (response.status_code != 200):
      time.sleep(WAIT_TIME)
      return get_daily_weather(lat, lng)

    return json.loads(response.text)
  except Exception as e:
    logger.log_error('get_daily_weather():', e)


##
# Formats a key/value pair with indentions for formatting and printing out
# with a temperature conversion from Celcius to Fahrenheit.
#
# author: mjhwa@yahoo.com
##
def output_fahrenheit(key, value, indent):
  return output(key, str((value * 9 / 5) + 32) + ' (F)', indent)


##
# Formats a key/value pair with indentions for formatting and printing out
# to a date and time format.
#
# author: mjhwa@yahoo.com
##
def output_date(key, value, indent):
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
def print_json(json_obj, level):
  offset = ''
  offset += '  ' * level

  if (isinstance(json_obj, dict) == True):
    for key in json_obj:

      value = json_obj[key]
      if ((isinstance(value, dict) == True) or (isinstance(value, list) == True)):
        print(offset + key)
        print_json(value, level + 1)
      else:
        print (offset + key + ' = ' + str(value))
  elif (isinstance(json_obj, list) == True):
    for x in json_obj:

      if (isinstance(x, list) == True):
        for key, value in x.items():
          print(offset + key)
          print_json(value, level + 1)
      else:
        print_json(x, level)
  else:
    print (offset + str(json_obj))


class NewlineFormatter(argparse.HelpFormatter):
    def _split_lines(self, text, width):
        # Adds a newline after every help text line
        return super()._split_lines(text, width) + ['']


def main(parser):
  args = parser.parse_args()

  if (args.current):
    data = get_current_weather(PRIMARY_LAT, PRIMARY_LNG)
    print_json(data, 0)
  elif (args.daily):
    data = get_daily_weather(PRIMARY_LAT, PRIMARY_LNG)
    print_json(data, 0)
  elif (args.distance):
    print(
      'distance from primary location (mi): ' 
      + str(
        get_distance(
          args.distance[0], 
          args.distance[1], 
          PRIMARY_LAT,
          PRIMARY_LNG
        )
      )
    )
  else:
    parser.print_help()


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
                    prog='utilities.py',
                    description='Commonly used and helpful tools.',
                    formatter_class=NewlineFormatter)
  group = parser.add_mutually_exclusive_group()
  group.add_argument(
                     '-c', 
                     '--current', 
                     help='prints current weather conditions at a configured primary location',
                     action='store_true'
                    )
  group.add_argument(
                     '-d', 
                     '--daily', 
                     help='prints weather conditions for today + 7 days, and hourly weather conditions for 48 hours '
                          'at a configured primary location',
                     action='store_true'
                    )
  group.add_argument(
#                     '-D', 
                     '--distance', 
                     help='calculates distance from a configured primary location; LATITUDE and LONGITUDE is a location '
                          'in decimal degrees',
                     type=float,
                     nargs=2,
                     metavar=('LATITUDE', 'LONGITUDE')
                    )

  main(parser)


import common.logger as logger