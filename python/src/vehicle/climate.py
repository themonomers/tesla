import argparse
import vehicle.api as api

from vehicle.api import (
  get_vehicle_data, 
  set_temp, 
  set_seat_heating, 
  set_seat_cooling)
from common.googleutil import get_google_sheet_service
from common.utilities import (
  is_vehicle_at_primary, 
  get_today_time, 
  get_current_weather,
  delete_cron,
  create_cron)
from common.argutil import CustomHelpFormatter
from common.logutil import log
from common.configutil import config
from common.constants import (
  M3_VIN,
  MX_VIN,
  EV_SPREADSHEET_ID,
  PRIMARY_LAT,
  PRIMARY_LNG)
from datetime import datetime


##
# Creates a trigger to precondition the cabin for the following morning, 
# based on if the car is at the primary location and if "Eco Mode" is off 
# similar to how Nest thermostats work for vacation scenarios.  With the 
# new endpoints released, you can achieve the same functionality by setting 
# scheduled departure for preconditioning.  I decided to keep this code 
# running as I don't drive long distances so the added feature of 
# preconditioning the battery, in addition to the cabin, is a waste of 
# energy (entropy) for me.
#
# author: mjhwa@yahoo.com
## 
def set_precondition(data, eco_mode, start_time):
  vin = data['response']['vin']

  # check if eco mode is off first so we don't have to even call the 
  # Tesla API if we don't have to
  if eco_mode == 'off':
    # check if the car is with 0.25 miles of the primary location
    if is_vehicle_at_primary(data):
      # create precondition start crontab at preferred time tomorrow
      delete_cron(config['cron']['climate_start'] + ('m3' if vin == M3_VIN else 'mx') + ' ' + config['cron']['redirect'])
      create_cron(config['cron']['climate_start'] + ('m3' if vin == M3_VIN else 'mx') + ' ' + config['cron']['redirect'], 
                  start_time.month, 
                  start_time.day, 
                  start_time.hour, 
                  start_time.minute)
      return start_time
  return None


##
# Checks a Google Sheet for heating and cooling preferences and sends a command 
# to precondition the car.  Includes seat heating preferences. Originally this 
# just used the inside car temp but to also account for the outside temperature, 
# it might be more comfortable for the occupants to look at the average of the 
# two to determine when to pre-heat/cool.
#
# Trying to use a weather API instead of the inside or outside temp data from 
# the cars.  The temp data from the cars don't seem to be accurate enough 
# and not representative of passenger comfort of when to pre-heat/cool.
#
# author: mjhwa@yahoo.com
##
def start_m3_precondition():
  try:
    # get configuration info
    service = get_google_sheet_service()
    climate_config = service.spreadsheets().values().get(
      spreadsheetId=EV_SPREADSHEET_ID, 
      range='Climate!A3:P22'
    ).execute().get('values', [])
    service.close()

    # check if eco mode is on first so we don't have to even call the Tesla API if we don't have to
    if climate_config[19][1] == 'on': return
    
    # get local weather
    wdata = get_current_weather(PRIMARY_LAT, PRIMARY_LNG)
    log().debug('temp: ' + str(wdata['current']['temp']))
    
    log().debug('cold temp threshold: ' + climate_config[17][1])
    log().debug('hot temp threshold: ' + climate_config[18][1])

    # get today's day of week to compare against Google Sheet temp preferences 
    # for that day
    day_of_week = datetime.today().strftime('%A')
    dow_index = [index for index, element in enumerate(climate_config) if day_of_week in element]
    seats = []
    mode = ''
    
    # compare temp readings and threshold to determine heating or cooling temps 
    # to use
    if wdata['current']['temp'] < float(climate_config[17][1]):
      # get pre-heat preferences  
      try:
        d_temp = float(climate_config[dow_index[0]][1])
        p_temp = float(climate_config[dow_index[0]][2])
      except ValueError:
        return

      seats.append(climate_config[dow_index[0]][3])
      seats.append(climate_config[dow_index[0]][4])
      seats.append(climate_config[dow_index[0]][5])
      seats.append(-1) # placeholder for index 3 as it's not assigned in the API
      seats.append(climate_config[dow_index[0]][6])
      seats.append(climate_config[dow_index[0]][7])

      if climate_config[dow_index[0]][9] == 'skip':
        return
      else:
        stop_time = get_today_time(climate_config[dow_index[0]][9])  

      mode = 'heat'
    elif wdata['current']['temp'] > float(climate_config[18][1]):
      # get pre-cool preferences
      try:
        d_temp = float(climate_config[dow_index[1]][1])
        p_temp = float(climate_config[dow_index[1]][2])
      except ValueError:
        return

      seats.append(climate_config[dow_index[1]][3])
      seats.append(climate_config[dow_index[1]][4])

      if climate_config[dow_index[1]][9] == 'skip':
        return
      else:
        stop_time = get_today_time(climate_config[dow_index[1]][9])

      mode = 'cool'
    else:
      return # outside temp is within cold and hot thresholds so no preconditioning required; inside and outside car temp readings seem to be inaccurate until the HVAC runs

    log().debug('d_temp: ' + str(d_temp))
    log().debug('p_temp: ' + str(p_temp))
    log().debug('seats: ' + str(seats))
    # no need to execute if the car is not at primary location
    data = get_vehicle_data(M3_VIN)
    if is_vehicle_at_primary(data):
      # send command to start auto conditioning
      api.start_precondition(M3_VIN)

      # set driver and passenger temps
      set_temp(M3_VIN, d_temp, p_temp)
      
      # set seat heater settings
      for index, item in enumerate(seats):
        if index == 3:
          continue # skip index 3 as it's not assigned in the API
        set_seat_cooling(M3_VIN, int(index + 1), 
                         int(item)) if mode == 'cool' else set_seat_heating(M3_VIN, int(index), int(item))

      # create crontab to stop preconditioning at preferred time later in the day
      setup_stop_cron(M3_VIN, stop_time)
  except Exception as e:
    log().error('start_m3_precondition(): ' + str(e))


def start_mx_precondition():
  try:
    # get configuration info
    service = get_google_sheet_service()
    climate_config = service.spreadsheets().values().get(
      spreadsheetId=EV_SPREADSHEET_ID, 
      range='Climate!A3:P22'
    ).execute().get('values', [])
    service.close()

    # check if eco mode is on first so we don't have to even call the Tesla API if we don't have to
    if climate_config[19][10] == 'on': return
    
    # get local weather
    wdata = get_current_weather(PRIMARY_LAT, PRIMARY_LNG)
    log().debug('temp: ' + str(wdata['current']['temp']))    

    log().debug('cold temp threshold: ' + climate_config[17][10])
    log().debug('hot temp threshold: ' + climate_config[18][10])

    # get today's day of week to compare against Google Sheet temp preferences 
    # for that day
    day_of_week = datetime.today().strftime('%A')
    dow_index = [index for index, element in enumerate(climate_config) if day_of_week in element]
    seats = []
    
    # compare temp readings and threshold to determine heating or cooling temps 
    # to use
    if wdata['current']['temp'] < float(climate_config[17][10]):
      # get pre-heat preferences
      try:
        d_temp = float(climate_config[dow_index[0]][10])
        p_temp = float(climate_config[dow_index[0]][11])
      except ValueError:
        return

      seats.append(climate_config[dow_index[0]][12])
      seats.append(climate_config[dow_index[0]][13])

      if climate_config[dow_index[0]][15] == 'skip':
        return
      else:
        stop_time = get_today_time(climate_config[dow_index[0]][15])
    elif wdata['current']['temp'] > float(climate_config[18][10]):
      # get pre-cool preferences
      try:
        d_temp = float(climate_config[dow_index[1]][10])
        p_temp = float(climate_config[dow_index[1]][11])
      except ValueError:
        return

      seats.append(climate_config[dow_index[1]][12])
      seats.append(climate_config[dow_index[1]][13])

      if climate_config[dow_index[1]][15] == 'skip':
        return
      else:
        stop_time = get_today_time(climate_config[dow_index[1]][15])
    else:
      return # outside temp is within cold and hot thresholds so no preconditioning required; inside and outside car temp readings seem to be inaccurate until the HVAC runs

    log().debug('d_temp: ' + str(d_temp))
    log().debug('p_temp: ' + str(p_temp))
    log().debug('seats: ' + str(seats))
    # no need to execute if the car is not at primary location
    data = get_vehicle_data(MX_VIN)
    if is_vehicle_at_primary(data):
      # send command to start auto conditioning
      api.start_precondition(MX_VIN)

      # set driver and passenger temps
      set_temp(MX_VIN, d_temp, p_temp)

      # set seat heater settings
      for index, item in enumerate(seats):
        set_seat_heating(MX_VIN, int(index), int(item))
      
      # create crontab to stop preconditioning at preferred time later in the day
      setup_stop_cron(MX_VIN, stop_time)
  except Exception as e: 
    log().error('start_mx_precondition(): ' + str(e))


def setup_stop_cron(vin, stop_time):
  delete_cron(config['cron']['climate_stop'] + ('m3' if vin == M3_VIN else 'mx') + ' ' + config['cron']['redirect'])
  create_cron(config['cron']['climate_stop'] + ('m3' if vin == M3_VIN else 'mx') + ' ' + config['cron']['redirect'], 
              stop_time.month, 
              stop_time.day, 
              stop_time.hour, 
              stop_time.minute)

##
# Sends command to stop vehicle preconditioning based on a previously scheduled
# crontab configured in a Google Sheet.
#
# author: mjhwa@yahoo.com
##
def stop_precondition(vin):
  try:
    data = get_vehicle_data(vin)
    if (is_vehicle_at_primary(data)
        and data['response']['drive_state']['shift_state'] not in {'D', 'R', 'N'}): # only execute if the car is at primary location and in park
      api.stop_precondition(vin)
  except Exception as e:
    log().error('stop_precondition(' + vin + '): ' + str(e))


def main(parser):
  args = parser.parse_args()

  if args.start:
    if args.start[0] == 'm3':
      start_m3_precondition()
    elif args.start[0] == 'mx':
      start_mx_precondition()
    else:
      parser.error('invalid VEHICLE type, must be \'m3\' or \'mx\'')
  elif args.stop:
    if args.stop[0] == 'm3':
      stop_precondition(M3_VIN)
    elif args.stop[0] == 'mx':
      stop_precondition(MX_VIN)
    else:
      parser.error('invalid VEHICLE type, must be \'m3\' or \'mx\'')
  else:
    parser.print_help()


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
                    prog='climate.py',
                    description='Sets up crontab for starting the car HVAC based on references stored in a Google Sheet.',
                    formatter_class=CustomHelpFormatter)
  group = parser.add_mutually_exclusive_group()
  group.add_argument(
                     '-t', 
                     '--start', 
                     help='starts pre-conditioning for a vehicle; VEHICLE can be \'m3\' or \'mx\'',
                     nargs=1,
                     metavar='VEHICLE'
                    )
  group.add_argument(
                     '-p', 
                     '--stop', 
                     help='stops pre-conditioning for a vehicle; VEHICLE can be \'m3\' or \'mx\'',
                     nargs=1,
                     metavar='VEHICLE'
                    )

  main(parser)