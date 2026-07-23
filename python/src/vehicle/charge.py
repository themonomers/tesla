import time
import argparse

from vehicle.api import (
  get_vehicle_data, 
  add_charge_schedule, 
  remove_charge_schedule, 
  start_charge, 
  stop_charge)
from vehicle.climate import set_precondition
from common.googleutil import get_google_sheet_service
from common.emailutil import send_email
from common.utilities import (
  is_vehicle_at_primary, 
  is_vehicle_at_secondary, 
  get_tomorrow_time,
  delete_cron,
  create_cron)
from common.argutil import CustomHelpFormatter
from common.logutil import log
from common.configutil import encrypted_config, config
from common.constants import (
  EV_SPREADSHEET_ID,
  WAIT_TIME,
  M3_VIN,
  MX_VIN,
  EMAIL_1,
  CHARGING_STATE_COMPLETE)
from datetime import timedelta, datetime
from collections import namedtuple

EMAIL_2 = encrypted_config['notification']['email_2']
MX_FULL_CHARGE_RATE_AT_PRIMARY = 25  # (mi/hr)
M3_FULL_CHARGE_RATE_AT_PRIMARY = 37  # (mi/hr)
MX_FULL_CHARGE_RATE_AT_SECONDARY = 20  # (mi/hr)
M3_FULL_CHARGE_RATE_AT_SECONDARY = 30  # (mi/hr)
EARLIEST_CHARGING_START_TIME = '00:00'
CHARGING_STATE_CHARGING = 'Charging'


##
# Checks to see if the vehicles are plugged in, inferred from the charge 
# port door status, and sends an email to notify if it's not.  Also sets 
# scheduled charging time to start charging at the calculated date and time. 
# Skips if it's not within 0.25 miles from the primary location.
#
# If one of the other cars is in the secondary location, set time charge 
# start time based on the secondary charge rate and set the charge start 
# time for the one at the primary location to charge at full charge rate. 
#
# author: mjhwa@yahoo.com
##
def notify_is_tesla_plugged_in():
  try:
    try:
      # get charging configuration info
      service = get_google_sheet_service()
      charge_config = service.spreadsheets().values().get(
        spreadsheetId=EV_SPREADSHEET_ID, 
        range='Charge!A3:C11'
      ).execute().get('values', [])

      # get climate configuration info
      climate_config = service.spreadsheets().values().get(
        spreadsheetId=EV_SPREADSHEET_ID, 
        range='Climate!A3:P22'
      ).execute().get('values', [])
      service.close()
    except Exception as e:
      log().warning('Retry getting configuration info from Google Sheets: ' + str(e))
      time.sleep(WAIT_TIME)
      notify_is_tesla_plugged_in()

    # get all vehicle data to avoid repeat API calls
    m3_data = get_vehicle_data(M3_VIN)
    mx_data = get_vehicle_data(MX_VIN)

    # send email notification if the car is not plugged in
    charge_port_door_open = m3_data['response']['charge_state']['charge_port_door_open']
    battery_level = m3_data['response']['charge_state']['battery_level']
    battery_range = m3_data['response']['charge_state']['battery_range']
    send_plugged_in_message('Model 3', 
                            battery_level, 
                            battery_range, 
                            charge_port_door_open, 
                            charge_config[8][1],
                            EMAIL_1,
                            '',
                            '') 

    charge_port_door_open = mx_data['response']['charge_state']['charge_port_door_open']
    battery_level = mx_data['response']['charge_state']['battery_level']
    battery_range = mx_data['response']['charge_state']['battery_range']
    send_plugged_in_message('Model X', 
                            battery_level, 
                            battery_range, 
                            charge_port_door_open, 
                            charge_config[8][2],
                            EMAIL_2,
                            '',
                            EMAIL_1) 

    # set cars for scheduled charging by daily charge time preference
    day_of_week = (datetime.today() + timedelta(1)).strftime('%A')
    dow_index = [index for index, element in enumerate(charge_config) if day_of_week in element]
    m3_target_finish_time = get_tomorrow_time(charge_config[dow_index[0]][1])
    mx_target_finish_time = get_tomorrow_time(charge_config[dow_index[0]][2])
    m3_charge_start_time = schedule_m3_charging(m3_data, mx_data, m3_target_finish_time, mx_target_finish_time)
    mx_charge_start_time = schedule_mx_charging(m3_data, mx_data, m3_target_finish_time, mx_target_finish_time)

    # set cabin preconditioning the next morning and check that it's not 
    # "skip"
    m3_climate_start_time = None
    mx_climate_start_time = None
    dow_index = [index for index, element in enumerate(climate_config) if day_of_week in element]
    if (climate_config[dow_index[0]][8] != 'skip'):
      m3_climate_start_time = get_tomorrow_time(climate_config[dow_index[0]][8])
      m3_climate_start_time = set_precondition(m3_data, climate_config[19][1], m3_climate_start_time)
    if (climate_config[dow_index[0]][14] != 'skip'):
      mx_climate_start_time = get_tomorrow_time(climate_config[dow_index[0]][14])
      mx_climate_start_time = set_precondition(mx_data, climate_config[19][10], mx_climate_start_time)

    # send email notification if either charging or preconditioning is scheduled
    send_scheduled_charge_message('Model 3',
                                  m3_data,
                                  m3_charge_start_time,
                                  m3_target_finish_time,
                                  m3_climate_start_time,
                                  EMAIL_1,
                                  '',
                                  '')
    send_scheduled_charge_message('Model X',
                                  mx_data,
                                  mx_charge_start_time,
                                  mx_target_finish_time,
                                  mx_climate_start_time,
                                  EMAIL_1,
                                  '',
                                  '')
  except Exception as e:
    log().error('notify_is_tesla_plugged_in(): ' + str(e))
    

##
# Called by a crontab to read vehicle range and expected charge 
# finish time from a Google Sheet, then call the API to set a time 
# for scheduled charging in the vehicle.
#
# author: mjhwa@yahoo.com
##
def schedule_m3_charging(m3_data, mx_data, m3_target_finish_time, mx_target_finish_time): 
  if (m3_data['response']['charge_state']['charging_state'] != CHARGING_STATE_COMPLETE):
    # get calculated start time depending on location of cars
    if (is_vehicle_at_primary(m3_data) == True
        and is_vehicle_at_primary(mx_data) == True):
      start_time = calculate_scheduled_charging('m3_primary_shared_charging', 
                                                m3_data, 
                                                mx_data, 
                                                m3_target_finish_time, 
                                                mx_target_finish_time)
    elif (is_vehicle_at_primary(m3_data) == True 
          and is_vehicle_at_primary(mx_data) == False):
      start_time = calculate_scheduled_charging('m3_primary_full_rate', 
                                                m3_data, 
                                                mx_data, 
                                                m3_target_finish_time, 
                                                mx_target_finish_time)
    elif (is_vehicle_at_secondary(m3_data)):
      start_time = calculate_scheduled_charging('m3_secondary_full_rate', 
                                                m3_data, 
                                                mx_data, 
                                                m3_target_finish_time, 
                                                mx_target_finish_time)
    else:
      return None

    total_minutes = (start_time.hour * 60) + start_time.minute

    # Remove any previous charge schedule by this program, id=1.
    remove_charge_schedule(M3_VIN, 1)
    add_charge_schedule(M3_VIN, 
                        m3_data['response']['drive_state']['latitude'], 
                        m3_data['response']['drive_state']['longitude'], 
                        total_minutes, 
                        1)
    stop_charge(M3_VIN) # for some reason charging starts sometimes after add_charge_schedule API is called

    schedule_backup_charging(m3_data, start_time + timedelta(minutes = 10))

    return start_time
  else:
    return None


def schedule_mx_charging(m3_data, mx_data, m3_target_finish_time, mx_target_finish_time): 
  if (mx_data['response']['charge_state']['charging_state'] != CHARGING_STATE_COMPLETE):
    # get calculated start time depending on location of cars
    if (is_vehicle_at_primary(mx_data) == True 
        and is_vehicle_at_primary(m3_data) == True):
      start_time = calculate_scheduled_charging('mx_primary_shared_charging',
                                                m3_data, 
                                                mx_data, 
                                                m3_target_finish_time, 
                                                mx_target_finish_time)
    elif (is_vehicle_at_primary(mx_data) == True 
          and is_vehicle_at_primary(m3_data) == False):
      start_time = calculate_scheduled_charging('mx_primary_full_rate', 
                                                m3_data, 
                                                mx_data, 
                                                m3_target_finish_time, 
                                                mx_target_finish_time)
    elif (is_vehicle_at_secondary(mx_data)):
      start_time = calculate_scheduled_charging('mx_secondary_full_rate', 
                                                m3_data, 
                                                mx_data, 
                                                m3_target_finish_time, 
                                                mx_target_finish_time)
    else:
      return None

    total_minutes = (start_time.hour * 60) + start_time.minute

    remove_charge_schedule(MX_VIN, 1)
    add_charge_schedule(MX_VIN, 
                        mx_data['response']['drive_state']['latitude'], 
                        mx_data['response']['drive_state']['longitude'], 
                        total_minutes, 
                        1)
    stop_charge(MX_VIN)

    schedule_backup_charging(mx_data, start_time + timedelta(minutes = 10))

    return start_time
  else:
    return None


##
# Schedule vehicle charging based on start time.  Assumes
# the crontab scheduled charging based on finish time has 
# already run and preconditioning does not need to be set 
# again.
#
# author: mjhwa@yahoo.com
##
def charge_earliest():
  # get all vehicle data to avoid repeat API calls
  m3_data = get_vehicle_data(M3_VIN)
  mx_data = get_vehicle_data(MX_VIN)

  finish_times = calculate_finish_time(m3_data, mx_data)
  m3_finish_time = finish_times['m3_finish_time']
  mx_finish_time = finish_times['mx_finish_time']

  print('Charging at earliest off-peak time')
  print('==================================')
  print('Start time:  ' + get_tomorrow_time(EARLIEST_CHARGING_START_TIME).strftime('%B %d, %Y %I:%M %p'))
  print('Model 3 estimated finish time:  ' + m3_finish_time.strftime('%B %d, %Y %I:%M %p'))
  print('Model X estimated finish time:  ' + mx_finish_time.strftime('%B %d, %Y %I:%M %p'))
  confirm = input('\nDo you want to override scheduled departure to scheduled start at earliest off-peak time (y/N)?: ')
  if confirm == 'y':
    # set cars for scheduled charging at the earliest off-peak time
    m3_start_time = schedule_earliest_charging(m3_data)
    mx_start_time = schedule_earliest_charging(mx_data)

    confirm = input('\nDo you want email confirmation (y/N])?: ')
    if confirm == 'y':
      send_scheduled_charge_message('Model 3',
                                    m3_data,
                                    m3_start_time,
                                    m3_finish_time,
                                    None,
                                    EMAIL_1,
                                    '',
                                    '')
      send_scheduled_charge_message('Model X',
                                    mx_data,
                                    mx_start_time,
                                    mx_finish_time,
                                    None,
                                    EMAIL_1,
                                    '',
                                    '')
    else:
      print('\nNo email confirmation')
  else:
    print('\nScheduled start canceled')


##
# Schedule charging based on earliest time for off-peak rates.
#
# author: mjhwa@yahoo.com
##
def schedule_earliest_charging(data): 
  vin = data['response']['vin']

  if (data['response']['charge_state']['charging_state'] != CHARGING_STATE_COMPLETE 
      and is_vehicle_at_primary(data) == True):
    start_time = get_tomorrow_time(EARLIEST_CHARGING_START_TIME)
    total_minutes = (start_time.hour * 60) + start_time.minute

    remove_charge_schedule(vin, 1)
    add_charge_schedule(vin, 
                        data['response']['drive_state']['latitude'], 
                        data['response']['drive_state']['longitude'], 
                        total_minutes, 
                        1)
    stop_charge(vin)

    schedule_backup_charging(data, start_time + timedelta(minutes = 10))

    return start_time
  else:
    return None


##
# Additional scheduled charging check run on crontab.  If it failed to start, this
# will attempt to start it at the target time.
#
# author: mjhwa@yahoo.com
def check_charge(vin):
  try:
    data = get_vehicle_data(vin)

    if (is_vehicle_at_primary(data) 
        and data['response']['charge_state']['charging_state'] != CHARGING_STATE_CHARGING
        and (data['response']['charge_state']['charging_state'] != CHARGING_STATE_COMPLETE 
             or data['response']['charge_state']['battery_level'] <= data['response']['charge_state']['charge_limit_soc'])):
      log().warning('check_charge(' + vin + '): Scheduled charging failed to start.  Starting backup charging.')
      start_charge(vin)
  except Exception as e:
    log().error('check_charge(' + vin + '): ' + str(e))


##
# Create a crontab to check if scheduled charging has started.
#
# author: mjhwa@yahoo.com
##
def schedule_backup_charging(data, start_time):
  vin = data['response']['vin']

  if (is_vehicle_at_primary(data)):
    # create backup charging start crontab at target time tomorrow
    delete_cron(config['cron']['charge_check'] + ('m3' if vin == M3_VIN else 'mx') + ' ' + config['cron']['redirect'])
    create_cron(config['cron']['charge_check'] + ('m3' if vin == M3_VIN else 'mx') + ' ' + config['cron']['redirect'], 
                start_time.month, 
                start_time.day, 
                start_time.hour, 
                start_time.minute)


##
# Calculates the scheduled charging time for 2 vehicles depending
# on their location, charge state, and finish time.
#
# author: mjhwa@yahoo.com
##
def calculate_scheduled_charging(scenario, m3_data, mx_data, m3_target_finish_time, mx_target_finish_time):
  miles_needed = calculate_miles_needed(m3_data, mx_data)
  mx_miles_needed = miles_needed['mx_miles_needed']
  m3_miles_needed = miles_needed['m3_miles_needed']

  # Calculate scheduled charging time based on location of cars
  if scenario == 'mx_primary_shared_charging' or scenario == 'm3_primary_shared_charging':
    mx_charging_time_at_full_rate = mx_miles_needed / MX_FULL_CHARGE_RATE_AT_PRIMARY  # hours
    m3_charging_time_at_full_rate = m3_miles_needed / M3_FULL_CHARGE_RATE_AT_PRIMARY  # hours

    mx_start_time_at_full_rate = mx_target_finish_time - timedelta(hours = mx_charging_time_at_full_rate)
    m3_start_time_at_full_rate = m3_target_finish_time - timedelta(hours = m3_charging_time_at_full_rate)

    # Determine if there is a charging time overlap
    Range = namedtuple('Range', ['start', 'end'])
    r1 = Range(start = mx_start_time_at_full_rate, end = mx_target_finish_time)
    r2 = Range(start = m3_start_time_at_full_rate, end = m3_target_finish_time)
    latest_start = max(r1.start, r2.start)
    earliest_end = min(r1.end, r2.end)
    delta = (earliest_end - latest_start).total_seconds()
    overlap = max(0, delta)

    # 1.  Charging times don't overlap
    #
    #                                     Charging at full rate   | 10:00
    # Car 1                           |===========================|
    # Car 2 |======================|
    #        Charging at full rate | 7:00
    if (overlap <= 0):
      if (scenario == 'm3_primary_shared_charging'): 
        return m3_start_time_at_full_rate

      if (scenario == 'mx_primary_shared_charging'): 
        return mx_start_time_at_full_rate
        
    else:
    # 2a.  Charging times overlap, fully with different finish times
    #
    #       Charging at 
    #       full rate                        Charging at full rate | 10:00
    # Car 1 |============|==============|==========================|
    # Car 2              |==============|
    #             Charging at half rate | 7:00
      if (mx_target_finish_time != m3_target_finish_time
          and (mx_start_time_at_full_rate < m3_start_time_at_full_rate and mx_target_finish_time > m3_target_finish_time
               or m3_start_time_at_full_rate < mx_start_time_at_full_rate and m3_target_finish_time > mx_target_finish_time)):
        # Find the longer session
        if (mx_target_finish_time - mx_start_time_at_full_rate).total_seconds() > (m3_target_finish_time - m3_start_time_at_full_rate).total_seconds():
          # Car 2
          m3_charging_time_at_half_rate = m3_miles_needed / (M3_FULL_CHARGE_RATE_AT_PRIMARY / 2)
          m3_start_time = m3_target_finish_time - timedelta(hours = m3_charging_time_at_half_rate)

          # Car 1
          mx_miles_added_at_full_rate = (mx_target_finish_time - m3_target_finish_time).total_seconds() / 60 / 60 * MX_FULL_CHARGE_RATE_AT_PRIMARY
          mx_miles_added_at_half_rate = m3_charging_time_at_half_rate * (MX_FULL_CHARGE_RATE_AT_PRIMARY / 2)
          mx_miles_remaining = mx_miles_needed - mx_miles_added_at_full_rate - mx_miles_added_at_half_rate
          mx_start_time = (mx_target_finish_time 
                            - timedelta(hours = mx_miles_added_at_full_rate / MX_FULL_CHARGE_RATE_AT_PRIMARY)
                            - timedelta(hours = mx_miles_added_at_half_rate / (MX_FULL_CHARGE_RATE_AT_PRIMARY / 2))
                            - timedelta(hours = mx_miles_remaining / MX_FULL_CHARGE_RATE_AT_PRIMARY)
                          )

        else:
          # Car 2
          mx_charging_time_at_half_rate = mx_miles_needed / (MX_FULL_CHARGE_RATE_AT_PRIMARY / 2)
          mx_start_time = mx_target_finish_time - timedelta(hours = mx_charging_time_at_half_rate)

          # Car 1
          m3_miles_added_at_full_rate = (m3_target_finish_time - mx_target_finish_time).total_seconds() / 60 / 60 * M3_FULL_CHARGE_RATE_AT_PRIMARY
          m3_miles_added_at_half_rate = mx_charging_time_at_half_rate * (M3_FULL_CHARGE_RATE_AT_PRIMARY / 2)
          m3_miles_remaining = m3_miles_needed - m3_miles_added_at_full_rate - m3_miles_added_at_half_rate
          m3_start_time = (m3_target_finish_time 
                            - timedelta(hours = m3_miles_added_at_full_rate / M3_FULL_CHARGE_RATE_AT_PRIMARY)
                            - timedelta(hours = m3_miles_added_at_half_rate / (M3_FULL_CHARGE_RATE_AT_PRIMARY / 2))
                            - timedelta(hours = m3_miles_remaining / M3_FULL_CHARGE_RATE_AT_PRIMARY)
                          )

    # 2b.  Charging times overlap, partially
    #
    #                                        Charging at full rate | 10:00
    # Car 1                      |=======|=========================|
    # Car 2 |====================|=======|
    #        Charging at full            | 7:00
    #        rate                Charging at 
    #                            half rate
      elif (mx_target_finish_time > m3_target_finish_time):
        # Car 1
        mx_miles_added_at_full_rate = ((mx_target_finish_time - m3_target_finish_time).total_seconds() 
                                        / 60 / 60 
                                        * MX_FULL_CHARGE_RATE_AT_PRIMARY)
        mx_miles_remaining = mx_miles_needed - mx_miles_added_at_full_rate
        mx_charging_time_at_half_rate = mx_miles_remaining / (MX_FULL_CHARGE_RATE_AT_PRIMARY / 2)  # hours
        mx_start_time = m3_target_finish_time - timedelta(hours = mx_charging_time_at_half_rate)

        # Car 2
        m3_miles_added_at_half_rate = ((m3_target_finish_time - mx_start_time).total_seconds()
                                        / 60 / 60 
                                        * (M3_FULL_CHARGE_RATE_AT_PRIMARY / 2))
        m3_miles_remaining = m3_miles_needed - m3_miles_added_at_half_rate
        m3_charging_time_at_full_rate = m3_miles_remaining / M3_FULL_CHARGE_RATE_AT_PRIMARY  # hours
        m3_start_time = mx_start_time - timedelta(hours = m3_charging_time_at_full_rate)

      elif (mx_target_finish_time < m3_target_finish_time):
        # Car 1
        m3_miles_added_at_full_rate = ((m3_target_finish_time - mx_target_finish_time).total_seconds() 
                                        / 60 / 60 
                                        * M3_FULL_CHARGE_RATE_AT_PRIMARY)
        m3_miles_remaining = m3_miles_needed - m3_miles_added_at_full_rate
        m3_charging_time_at_half_rate = m3_miles_remaining / (M3_FULL_CHARGE_RATE_AT_PRIMARY / 2)  # hours
        m3_start_time = mx_target_finish_time - timedelta(hours = m3_charging_time_at_half_rate)

        # Car 2
        mx_miles_added_at_half_rate = ((mx_target_finish_time - m3_start_time).total_seconds()
                                        / 60 / 60 
                                        * (MX_FULL_CHARGE_RATE_AT_PRIMARY / 2))
        mx_miles_remaining = mx_miles_needed - mx_miles_added_at_half_rate
        mx_charging_time_at_full_rate = mx_miles_remaining / MX_FULL_CHARGE_RATE_AT_PRIMARY  # hours
        mx_start_time = m3_start_time - timedelta(hours = mx_charging_time_at_full_rate)
    
    # 2c.  Charging times overlap, fully with the same finish times
    #          
    # For the longer/earlier start time, calculate the start time based on a part of 
    # the charging session being at half rate and another part at full rate.  The session 
    # will charge at half rate when the other car begins charging but the difference in 
    # miles/charge that starts before the other car will be at full rate.
    #
    #                                  Charging at half rate   | 07:00
    # Car 1                        |===========================|
    # Car 2 |======================|===========================|
    #        Charging at full rate 
      elif (mx_target_finish_time == m3_target_finish_time):
        mx_charging_time_at_half_rate = mx_miles_needed / (MX_FULL_CHARGE_RATE_AT_PRIMARY / 2)  # hours
        m3_charging_time_at_half_rate = m3_miles_needed / (M3_FULL_CHARGE_RATE_AT_PRIMARY / 2)  # hours

        mx_start_time_at_half_rate = mx_target_finish_time - timedelta(hours = mx_charging_time_at_half_rate)
        m3_start_time_at_half_rate = m3_target_finish_time - timedelta(hours = m3_charging_time_at_half_rate)

        if (mx_start_time_at_half_rate < m3_start_time_at_half_rate):
          # Car 1 (The shorter/later start time will charge at half rate the entire session)
          m3_start_time = m3_start_time_at_half_rate

          # Car 2
          mx_miles_added_at_half_rate = ((mx_target_finish_time - m3_start_time_at_half_rate).total_seconds() 
                                          / 60 / 60 
                                          * (MX_FULL_CHARGE_RATE_AT_PRIMARY / 2))
          mx_miles_remaining = mx_miles_needed - mx_miles_added_at_half_rate
          mx_miles_remaining_charging_time_at_full_rate = mx_miles_remaining / MX_FULL_CHARGE_RATE_AT_PRIMARY
          mx_start_time = m3_start_time_at_half_rate - timedelta(hours = mx_miles_remaining_charging_time_at_full_rate)
        else:
          # Car 1 (The shorter/later start time will charge at half rate the entire session)
          mx_start_time = mx_start_time_at_half_rate

          # Car 2
          m3_miles_added_at_half_rate = ((m3_target_finish_time - mx_start_time_at_half_rate).total_seconds() 
                                          / 60 / 60 
                                          * (M3_FULL_CHARGE_RATE_AT_PRIMARY / 2))
          m3_miles_remaining = m3_miles_needed - m3_miles_added_at_half_rate
          m3_miles_remaining_charging_time_at_full_rate = m3_miles_remaining / M3_FULL_CHARGE_RATE_AT_PRIMARY
          m3_start_time = mx_start_time_at_half_rate - timedelta(hours = m3_miles_remaining_charging_time_at_full_rate)

      if (scenario == 'm3_primary_shared_charging'): 
        return m3_start_time

      if (scenario == 'mx_primary_shared_charging'): 
        return mx_start_time
  elif (scenario == 'mx_primary_full_rate'):
    mx_start_time = mx_target_finish_time - timedelta(hours = (mx_miles_needed / MX_FULL_CHARGE_RATE_AT_PRIMARY))
    
    return mx_start_time
  elif (scenario == 'm3_primary_full_rate'):
    m3_start_time = m3_target_finish_time - timedelta(hours = (m3_miles_needed / M3_FULL_CHARGE_RATE_AT_PRIMARY))
    
    return m3_start_time
  elif (scenario == 'mx_secondary_full_rate'):
    mx_start_time = mx_target_finish_time - timedelta(hours = (mx_miles_needed / MX_FULL_CHARGE_RATE_AT_SECONDARY))
    
    return mx_start_time
  elif (scenario == 'm3_secondary_full_rate'):
    m3_start_time = m3_target_finish_time - timedelta(hours = (m3_miles_needed / M3_FULL_CHARGE_RATE_AT_SECONDARY))

    return m3_start_time


##
# Calculates the finish time based on earlist off-peak start time.
#
# author: mjhwa@yahoo.com
##
def calculate_finish_time(m3_data, mx_data):
  miles_needed = calculate_miles_needed(m3_data, mx_data)

  # Calculate how long charging will take based on miles needed
  mx_charging_time_at_full_rate = miles_needed['mx_miles_needed'] / MX_FULL_CHARGE_RATE_AT_PRIMARY
  m3_charging_time_at_full_rate = miles_needed['m3_miles_needed'] / M3_FULL_CHARGE_RATE_AT_PRIMARY

  leftover_time = 0
  mx_charging_time = 0
  m3_charging_time = 0 
  if mx_charging_time_at_full_rate > m3_charging_time_at_full_rate:
    leftover_time = mx_charging_time_at_full_rate - m3_charging_time_at_full_rate

    mx_charging_time = (m3_charging_time_at_full_rate * 2) + leftover_time
    m3_charging_time = m3_charging_time_at_full_rate * 2
  elif mx_charging_time_at_full_rate < m3_charging_time_at_full_rate:
    leftover_time = m3_charging_time_at_full_rate - mx_charging_time_at_full_rate

    mx_charging_time = mx_charging_time_at_full_rate * 2
    m3_charging_time = (mx_charging_time_at_full_rate * 2) + leftover_time

  mx_finish_time = get_tomorrow_time(EARLIEST_CHARGING_START_TIME) + timedelta(hours = mx_charging_time)
  m3_finish_time = get_tomorrow_time(EARLIEST_CHARGING_START_TIME) + timedelta(hours = m3_charging_time)

  finish_times = {
      'mx_finish_time': mx_finish_time,
      'm3_finish_time': m3_finish_time
  }

  return finish_times


##
# Calculate how many miles are needed for charging based on 
# current range and charging % target.
#
# author: mjhwa@yahoo.com
##
def calculate_miles_needed(m3_data, mx_data):
  mx_current_range = mx_data['response']['charge_state']['battery_range']
  m3_current_range = m3_data['response']['charge_state']['battery_range']

  mx_max_range = (   mx_data['response']['charge_state']['battery_range'] 
                  / (mx_data['response']['charge_state']['battery_level'] / 100.0))
  m3_max_range = (   m3_data['response']['charge_state']['battery_range'] 
                  / (m3_data['response']['charge_state']['battery_level'] / 100.0))

  mx_charge_limit = mx_data['response']['charge_state']['charge_limit_soc'] / 100.0
  m3_charge_limit = m3_data['response']['charge_state']['charge_limit_soc'] / 100.0

  mx_target_range = mx_max_range * mx_charge_limit
  m3_target_range = m3_max_range * m3_charge_limit

  mx_miles_needed = 0
  if (mx_target_range - mx_current_range) > 0: mx_miles_needed = mx_target_range - mx_current_range
  m3_miles_needed = 0
  if (m3_target_range - m3_current_range) > 0: m3_miles_needed = m3_target_range - m3_current_range

  miles_needed = {
      'mx_miles_needed': mx_miles_needed,
      'm3_miles_needed': m3_miles_needed
  }
  
  return miles_needed


def send_plugged_in_message(vehicle, battery_level, battery_range, charge_port_door_open, notify, to, cc, bcc):
  # check if email notification is set to "on" first 
  if (notify == 'on'):
    # send an email if the charge port door is not open, i.e. not plugged in
    if (charge_port_door_open == False):
      message = ('Your car is not plugged in.  \n\nCurrent battery level is '
                  + str(battery_level) 
                  + '%, '
                  + str(battery_range) 
                  + ' estimated miles.  \n\n-Your ' + vehicle)
      send_email('Please Plug In Your ' + vehicle, 
                 message, 
                 to,
                 cc,
                 bcc, 
                 '')
      log().debug('send email: ' + message)


def send_scheduled_charge_message(vehicle, data, charge_start_time, finish_time, climate_start_time, to, cc, bcc):
  message = ''
  subject = ''

  if charge_start_time != None:
    message = ('The ' + vehicle + ' is set to charge at ' 
                + charge_start_time.strftime('%B %d, %Y %H:%M')
                + ' to '
                + str(data['response']['charge_state']['charge_limit_soc']) + '%'
                + ' by ' + finish_time.strftime('%H:%M') + ', ' 
                + str(round(data['response']['charge_state']['battery_range']
                      / data['response']['charge_state']['battery_level']
                      * data['response']['charge_state']['charge_limit_soc']))  + ' miles of estimated range.  '
                + 'The ' + vehicle + ' is currently at '
                + str(data['response']['charge_state']['battery_level']) + '%, '
                + str(round(data['response']['charge_state']['battery_range'])) + ' miles of estimated range.\n\n')
  
  if climate_start_time != None:
    message += ('Preconditioning is set to start at ' + climate_start_time.strftime('%B %d, %Y %H:%M') + '.')

  if charge_start_time != None or climate_start_time != None:
    if charge_start_time != None and climate_start_time != None:
      subject = vehicle + ' Set to Charge and Precondition'
    elif charge_start_time != None and climate_start_time == None:
      subject = vehicle + ' Set to Charge'
    elif charge_start_time == None and climate_start_time != None:
      subject = vehicle + ' Set to Precondition'

    send_email(subject, 
               message, 
               to,
               cc,
               bcc, 
               '')


def main(parser):
  args = parser.parse_args()

  if (args.notify):
    notify_is_tesla_plugged_in()
  elif (args.check):
    if args.check[0] == 'm3':
      check_charge(M3_VIN)
    elif args.check[0] == 'mx':
      check_charge(MX_VIN)
    else:
      parser.error('invalid VEHICLE type, must be \'m3\' or \'mx\'')
  elif (args.earliest):
    charge_earliest()
  else:
    parser.print_help()


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
                    prog='charge.py',
                    description='Calculates and sets charging times to complete at a departure time for 2 EV\'s.',
                    formatter_class=CustomHelpFormatter)
  group = parser.add_mutually_exclusive_group()
  group.add_argument(
                     '-n', 
                     '--notify', 
                     help='checks if vehicles are plugged in and schedules charging and preconditioning',
                     action='store_true'
                    )
  group.add_argument(
                     '-c', 
                     '--check', 
                     help='backup charging if a vehicle isn\'t charging that\'s supposed to be; VEHICLE can be \'m3\' '
                          'or \'mx\'',
                     nargs=1,
                     metavar='VEHICLE'
                    )
  group.add_argument(
                     '-e', 
                     '--earliest', 
                     help='schedule charging at the earliest off-peak time',
                     action='store_true'
                    )

  main(parser)