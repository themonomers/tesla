import getopt, sys

from vehicle.api import get_vehicle_data, set_car_temp, set_car_seat_heating, set_car_seat_cooling, precondition_car_start, precondition_car_stop
from common.googleutil import get_google_sheet_service
from common.utilities import delete_cron_tab, create_cron_tab, is_vehicle_at_primary, get_today_time, get_current_weather, get_config
from common.logger import log_error
from datetime import datetime

config = get_config()
M3_VIN = config['vehicle']['m3_vin']
MX_VIN = config['vehicle']['mx_vin']
EV_SPREADSHEET_ID = config['google']['ev_spreadsheet_id'] 
PRIMARY_LAT = float(config['vehicle']['primary_lat'])
PRIMARY_LNG = float(config['vehicle']['primary_lng'])

WAIT_TIME = 30 


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
def set_m3_precondition(data, eco_mode, start_time):
  try: 
    # check if eco mode is off first so we don't have to even call the 
    # Tesla API if we don't have to
    if (eco_mode == 'off'):
      # check if the car is with 0.25 miles of the primary location
      if (is_vehicle_at_primary(data)):
        # create precondition start crontab at preferred time tomorrow
        delete_cron_tab('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/vehicle/climate.py --start=m3 >> /home/pi/tesla/python/cron.log 2>&1')
        create_cron_tab('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/vehicle/climate.py --start=m3 >> /home/pi/tesla/python/cron.log 2>&1', 
                        start_time.month, 
                        start_time.day, 
                        start_time.hour, 
                        start_time.minute)
        
        return start_time
    return None
  except Exception as e:
    log_error('set_m3_precondition():', e)


def set_mx_precondition(data, eco_mode, start_time):
  try: 
    # check if eco mode is off first so we don't have to even call the 
    # Tesla API if we don't have to
    if (eco_mode == 'off'):
      # check if the car is with 0.25 miles of the primary location
      if (is_vehicle_at_primary(data)):
        # create precondition start crontab at preferred time tomorrow
        delete_cron_tab('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/vehicle/climate.py --start=mx >> /home/pi/tesla/python/cron.log 2>&1')
        create_cron_tab('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/vehicle/climate.py --start=mx >> /home/pi/tesla/python/cron.log 2>&1', 
                        start_time.month, 
                        start_time.day, 
                        start_time.hour, 
                        start_time.minute)
        
        return start_time
    return None
  except Exception as e:
    log_error('set_mx_precondition():', e)


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
def precondition_m3_start():
  try:
    # get configuration info
    service = get_google_sheet_service()
    climate_config = service.spreadsheets().values().get(
      spreadsheetId=EV_SPREADSHEET_ID, 
      range='Climate!A3:P22'
    ).execute().get('values', [])
    service.close()

    # check if eco mode is on first so we don't have to even call the Tesla API if we don't have to
    if (climate_config[19][1] == 'on'): return
    
    # get local weather
    wdata = get_current_weather(PRIMARY_LAT, PRIMARY_LNG)
#    print('temp: ' + str(wdata['current']['temp']))
    
#    print('cold temp threshold: ' + climate_config[17][1])
#    print('hot temp threshold: ' + climate_config[18][1])

    # get today's day of week to compare against Google Sheet temp preferences 
    # for that day
    day_of_week = datetime.today().strftime('%A')
    dow_index = [index for index, element in enumerate(climate_config) if day_of_week in element]
    seats = []
    mode = ''
    
    # compare temp readings and threshold to determine heating or cooling temps 
    # to use
    if (wdata['current']['temp'] < float(climate_config[17][1])):
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
    elif (wdata['current']['temp'] > float(climate_config[18][1])):
      # get pre-cool preferences
      try:
        d_temp = float(climate_config[dow_index[1]][1])
        p_temp = float(climate_config[dow_index[1]][2])
      except ValueError:
        return

      seats.append(climate_config[dow_index[1]][3])
      seats.append(climate_config[dow_index[1]][4])
      seats.append(climate_config[dow_index[1]][5])
      seats.append(-1) # placeholder for index 3 as it's not assigned in the API
      seats.append(climate_config[dow_index[1]][6])
      seats.append(climate_config[dow_index[1]][7])

      if climate_config[dow_index[1]][9] == 'skip':
        return
      else:
        stop_time = get_today_time(climate_config[dow_index[1]][9])

      mode = 'cool'
    else:
      return # outside temp is within cold and hot thresholds so no preconditioning required; inside and outside car temp readings seem to be inaccurate until the HVAC runs

    #print('d_temp: ' + str(d_temp))
    #print('p_temp: ' + str(p_temp))
    #print('seats: ' + str(seats))
    # no need to execute if the car is not at primary location
    data = get_vehicle_data(M3_VIN)
    if (is_vehicle_at_primary(data)):
      # send command to start auto conditioning
      precondition_car_start(M3_VIN)

      # set driver and passenger temps
      set_car_temp(M3_VIN, d_temp, p_temp)
      
      # set seat heater settings
      for index, item in enumerate(seats):
        if (index == 3):
          continue # skip index 3 as it's not assigned in the API
        set_car_seat_cooling(M3_VIN, int(index), int(item)) if mode == 'cool' else set_car_seat_heating(M3_VIN, int(index), int(item))

      # create crontab to stop preconditioning at preferred time later in the day
      delete_cron_tab('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/vehicle/climate.py --stop=m3 >> /home/pi/tesla/python/cron.log 2>&1')
      create_cron_tab(
        '/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/vehicle/climate.py --stop=m3 >> /home/pi/tesla/python/cron.log 2>&1', 
        stop_time.month, 
        stop_time.day, 
        stop_time.hour, 
        stop_time.minute
      )
  except Exception as e:
    log_error('precondition_m3_start():', e)


def precondition_mx_start():
  try:
    # get configuration info
    service = get_google_sheet_service()
    climate_config = service.spreadsheets().values().get(
      spreadsheetId=EV_SPREADSHEET_ID, 
      range='Climate!A3:P22'
    ).execute().get('values', [])
    service.close()

    # check if eco mode is on first so we don't have to even call the Tesla API if we don't have to
    if (climate_config[19][10] == 'on'): return
    
    # get local weather
    wdata = get_current_weather(PRIMARY_LAT, PRIMARY_LNG)
#    print('temp: ' + str(wdata['current']['temp']))    

#    print('cold temp threshold: ' + climate_config[17][10])
#    print('hot temp threshold: ' + climate_config[18][10])

    # get today's day of week to compare against Google Sheet temp preferences 
    # for that day
    day_of_week = datetime.today().strftime('%A')
    dow_index = [index for index, element in enumerate(climate_config) if day_of_week in element]
    seats = []
    
    # compare temp readings and threshold to determine heating or cooling temps 
    # to use
    if (wdata['current']['temp'] < float(climate_config[17][10])):
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
    elif (wdata['current']['temp'] > float(climate_config[18][10])):
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

    #print('d_temp: ' + str(d_temp))
    #print('p_temp: ' + str(p_temp))
    #print('seats: ' + str(seats))
    # no need to execute if the car is not at primary location
    data = get_vehicle_data(MX_VIN)
    if (is_vehicle_at_primary(data)):
      # send command to start auto conditioning
      precondition_car_start(MX_VIN)

      # set driver and passenger temps
      set_car_temp(MX_VIN, d_temp, p_temp)

      # set seat heater settings
      for index, item in enumerate(seats):
        set_car_seat_heating(MX_VIN, int(index), int(item))
      
      # create crontab to stop preconditioning at preferred time later in the day
      delete_cron_tab('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/vehicle/climate.py --stop=mx >> /home/pi/tesla/python/cron.log 2>&1')
      create_cron_tab(
        '/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/vehicle/climate.py --stop=mx >> /home/pi/tesla/python/cron.log 2>&1', 
        stop_time.month, 
        stop_time.day, 
        stop_time.hour, 
        stop_time.minute
      )
  except Exception as e: 
    log_error('precondition_mx_start():', e)


##
# Sends command to stop vehicle preconditioning based on a previously scheduled
# crontab configured in a Google Sheet.
#
# author: mjhwa@yahoo.com
##
def precondition_m3_stop():
  precondition_stop(M3_VIN)


def precondition_mx_stop():
  precondition_stop(MX_VIN)


def precondition_stop(vin):
  try:
    data = get_vehicle_data(vin)
    if (is_vehicle_at_primary(data) and 
        data['response']['drive_state']['shift_state'] != 'D' and
        data['response']['drive_state']['shift_state'] != 'R' and
        data['response']['drive_state']['shift_state'] != 'N'): # only execute if the car is at primary location and in park
      precondition_car_stop(vin)
  except Exception as e:
    log_error('precondition_stop(' + vin + '):', e)


def print_help():
  print('Usage: python climate.py [OPTION...]')
  print('')
  print('--help                 prints the usage and options')
  print('')
  print('--start[=VEHICLE]      starts pre-conditioning for a vehicle;')
  print('                       VEHICLE can be \'m3\' or \'mx\'')
  print('')
  print('--stop[=VEHICLE]       stops pre-conditioning for a vehicle;')
  print('                       VEHICLE can be \'m3\' or \'mx\'')


def main():
  args = sys.argv[1:]
  options = ''
  long_options = ['help', 'start=', 'stop=']

  try:
    arguments, values = getopt.getopt(args, options, long_options)

    if len(arguments) < 1: print_help()

    for currentArg, currentVal in arguments:
      if currentArg in ('--help'):
        print_help()
      elif currentArg in ('--start'):
        if currentVal == 'm3':
          precondition_m3_start()
        elif currentVal == 'mx':
          precondition_mx_start()
        else:
          print_help()
      elif currentArg in ('--stop'):
        if currentVal == 'm3':
          precondition_m3_stop()
        elif currentVal == 'mx':
          precondition_mx_stop()
        else:
          print_help()
  except getopt.error as e:
    print_help()


if __name__ == "__main__":
  main()