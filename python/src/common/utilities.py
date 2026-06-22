import requests
import math
import json
import datetime
import time
import argparse

from common.googleutil import get_google_sheet_service
from common.argutil import CustomHelpFormatter
from common.logutil import log
from common.configutil import (
  encrypted_config, 
  config, 
  get_filepath)
from common.constants import (
  PRIMARY_LAT, 
  PRIMARY_LNG, 
  PAC, 
  WAIT_TIME)
from datetime import datetime, timedelta
from crontab import CronTab

SECONDARY_LAT = float(encrypted_config['vehicle']['secondary_lat'])
SECONDARY_LNG = float(encrypted_config['vehicle']['secondary_lng'])
OPENWEATHERMAP_KEY = encrypted_config['weather']['openweathermap_key']
LOG_SPREADSHEET_ID = encrypted_config['google']['log_spreadsheet_id']
BASE_WEATHER_URL = config['uri']['openweathermap_base_url']
R = 3958.8  #Earth radius in miles


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
    log().warning('is_vehicle_at_location(): ' + str(e))
    return False


def get_distance(car_lat, car_lng, x_lat, x_lng):
  diff_lat = to_rad(car_lat - x_lat)
  diff_lng = to_rad(car_lng - x_lng)  
  
  a = ((math.sin(diff_lat/2) * math.sin(diff_lat/2)) 
        + math.cos(x_lat) 
        * math.cos(car_lat) 
        * (math.sin(diff_lng/2) * math.sin(diff_lng/2)))
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
  d = R * c
  
  return d


def to_rad(x):
  return x * math.pi/180


##
# Helps format the charging or preconditioning time by defaulting the date.
#
# author: mjhwa@yahoo.com
##
def get_tomorrow_time(time):
  return datetime.strptime(
      str((datetime.now() + timedelta(1)).replace(tzinfo=PAC).year)
    + '-'
    + str((datetime.now() + timedelta(1)).replace(tzinfo=PAC).month)
    + '-'
    + str((datetime.now() + timedelta(1)).replace(tzinfo=PAC).day)
    + 'T'
    + time, '%Y-%m-%dT%H:%M'
  ).replace(tzinfo=PAC)


def get_today_time(time):
  return datetime.strptime(
      str(datetime.now().replace(tzinfo=PAC).year)
    + '-'
    + str(datetime.now().replace(tzinfo=PAC).month)
    + '-'
    + str(datetime.now().replace(tzinfo=PAC).day)
    + 'T'
    + time, '%Y-%m-%dT%H:%M'
  ).replace(tzinfo=PAC)


##
# Uses a free weather service with API to look up data by zipcode or other 
# attributes.  Gets current weather conditions.
#
# author: mjhwa@yahoo.com
##
def get_current_weather(lat, lng):
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
    

##
# Uses a free weather service with API to look up data by latitude and
# longitude or other attributes.  Gets daily weather conditions for 
# today + 7 days, and hourly weather conditions for 48 hours.
#
# author: mjhwa@yahoo.com
##
def get_daily_weather(lat, lng):
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


###
# Centralize repetitive HTTP Request calls.
#
# author: mjhwa@yahoo.com
##
def send_request(method, url, token, payload, cert):
  return requests.request(
    method,
    url, 
    **({'json': payload} if payload else {}),
    headers={'authorization': 'Bearer ' + token},
    **({'verify': cert} if cert else {})
  )


##
# Removes crontab for a single command.
#
# author: mjhwa@yahoo.com
##
def delete_cron(command):
  cron = CronTab(user='pi')
  job = cron.find_command(command)
  cron.remove(job)
  cron.write()


##
# Creates crontab entry for a single command.
#
# author: mjhwa@yahoo.com
##
def create_cron(command, month, day, hour, minute):
  cron = CronTab(user='pi')
  job = cron.new(command=command)
  job.month.on(month)
  job.day.on(day)
  job.hour.on(hour)
  job.minute.on(minute)
  cron.write()


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


##
# Load log file into Google Sheet for ease of viewing and analysis.
#
# author: mjhwa@yahoo.com
##
def load_log_into_gsheet(days_to_load):
  try:
    inputs = []
    count = 0
    threshold = get_today_time('00:00') - timedelta(days_to_load)

    with open(get_filepath('log_filename'), 'r') as file:
      for line in file:
        # Remove trailing newline characters
        clean_line = line.strip()
        
        # Split the line by spaces
        parts = clean_line.split(' ')
        
        # Extract fields based on index positions
        if len(parts) >= 4:
          timestamp = f"{parts[0]} {parts[1]}"
          level = parts[2]
          message = " ".join(parts[3:])

          log_date = datetime.strptime(str(timestamp), '%Y-%m-%d %H:%M:%S').replace(tzinfo=PAC)
          if log_date > threshold:
            # write this into Google Sheet
            inputs.append({
              'range': 'log!A' + str(2 + count),
              'values': [[level]]
            })
            inputs.append({
              'range': 'log!B' + str(2 + count),
              'values': [[timestamp]]
            })
            inputs.append({
              'range': 'log!C' + str(2 + count),
              'values': [[message]]
            })

            count = count + 1

    # clear sheet then batch write data
    if len(inputs) > 0:
      service = get_google_sheet_service()

      service.spreadsheets().values().batchClear(
          spreadsheetId=LOG_SPREADSHEET_ID, 
          body={'ranges': 'log!A2:C'}
      ).execute()

      service.spreadsheets().values().batchUpdate(
        spreadsheetId=LOG_SPREADSHEET_ID, 
        body={'data': inputs, 'valueInputOption': 'USER_ENTERED'}
      ).execute()
      service.close()

    file.close()
  except Exception as e:
    log().error('load_log_into_gsheet(): ' + str(e))


def main(parser):
  args = parser.parse_args()

  if (args.current):
    data = get_current_weather(PRIMARY_LAT, PRIMARY_LNG)
    print_json(data, 0)
  elif (args.daily):
    data = get_daily_weather(PRIMARY_LAT, PRIMARY_LNG)
    print_json(data, 0)
  elif (args.load):
    load_log_into_gsheet(args.load[0])
  else:
    parser.print_help()


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
                    prog='utilities.py',
                    description='Commonly used and helpful tools.',
                    formatter_class=CustomHelpFormatter)
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
                     '-l', 
                     '--load', 
                     help='load log file into Google Sheet for ease of viewing and analysis; DAYS are the number of days '
                          'of log entry history to load into Google Sheet',
                     type=int,
                     nargs=1,
                     metavar='DAYS'
                    )

  main(parser)