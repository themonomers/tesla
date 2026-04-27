import time
import getopt, sys

from TeslaVehicleAPI import getVehicleData, addChargeSchedule, removeChargeSchedule, startChargeVehicle, stopChargeVehicle
from GoogleAPI import getGoogleSheetService
from Email import sendEmail
from Climate import setM3Precondition, setMXPrecondition
from Utilities import isVehicleAtPrimary, isVehicleAtSecondary, getTomorrowTime, getConfig, deleteCronTab, createCronTab
from Logger import logInfo, logError, logErrorRetry, logErrorStdOut
from datetime import timedelta, datetime
from collections import namedtuple

config = getConfig()
M3_VIN = config['vehicle']['m3_vin']
MX_VIN = config['vehicle']['mx_vin']
EV_SPREADSHEET_ID = config['google']['ev_spreadsheet_id']
EMAIL_1 = config['notification']['email_1']
EMAIL_2 = config['notification']['email_2']

MX_FULL_CHARGE_RATE_AT_PRIMARY = 25  # (mi/hr)
M3_FULL_CHARGE_RATE_AT_PRIMARY = 37  # (mi/hr)
MX_FULL_CHARGE_RATE_AT_SECONDARY = 20  # (mi/hr)
M3_FULL_CHARGE_RATE_AT_SECONDARY = 30  # (mi/hr)
EARLIEST_CHARGING_START_TIME = '00:00'
WAIT_TIME = 30 


##
# Called by a crontab to read vehicle range and expected charge 
# finish time from a Google Sheet, then call the API to set a time 
# for scheduled charging in the vehicle.
#
# author: mjhwa@yahoo.com
##
def scheduleM3Charging(m3_data, mx_data, m3_target_finish_time, mx_target_finish_time): 
  try:
    if (m3_data['response']['charge_state']['charging_state'] != 'Complete'):
      # get calculated start time depending on location of cars
      if ((isVehicleAtPrimary(m3_data) == True) and
          (isVehicleAtPrimary(mx_data) == True)):
        start_time = calculateScheduledCharging('m3_primary_shared_charging', 
                                                m3_data, 
                                                mx_data, 
                                                m3_target_finish_time, 
                                                mx_target_finish_time)
      elif ((isVehicleAtPrimary(m3_data) == True) and 
            (isVehicleAtPrimary(mx_data) == False)):
        start_time = calculateScheduledCharging('m3_primary_full_rate', 
                                                m3_data, 
                                                mx_data, 
                                                m3_target_finish_time, 
                                                mx_target_finish_time)
      elif (isVehicleAtSecondary(m3_data)):
        start_time = calculateScheduledCharging('m3_secondary_full_rate', 
                                                m3_data, 
                                                mx_data, 
                                                m3_target_finish_time, 
                                                mx_target_finish_time)
      else:
        return None

      total_minutes = (start_time.hour * 60) + start_time.minute

      # Remove any previous scheduled charging by this program, temporarily set to
      # id=1, until I can figure out how to view the list of charge schedules and
      # their corresponding ID's.
      removeChargeSchedule(M3_VIN, 1)
      addChargeSchedule(M3_VIN, m3_data['response']['drive_state']['latitude'], m3_data['response']['drive_state']['longitude'], total_minutes, 1)
      stopChargeVehicle(M3_VIN) # for some reason charging starts sometimes after scheduled charging API is called

      scheduleBackupCharging(M3_VIN, m3_data, start_time + timedelta(minutes = 10))

      return start_time
    else:
      return None
  except Exception as e:
    logError('scheduleM3Charging():', e)


def scheduleMXCharging(m3_data, mx_data, m3_target_finish_time, mx_target_finish_time): 
  try:
    if (mx_data['response']['charge_state']['charging_state'] != 'Complete'):
      # get calculated start time depending on location of cars
      if ((isVehicleAtPrimary(mx_data) == True) and 
          (isVehicleAtPrimary(m3_data) == True)):
        start_time = calculateScheduledCharging('mx_primary_shared_charging',
                                                m3_data, 
                                                mx_data, 
                                                m3_target_finish_time, 
                                                mx_target_finish_time)
      elif ((isVehicleAtPrimary(mx_data) == True) and 
            (isVehicleAtPrimary(m3_data) == False)):
        start_time = calculateScheduledCharging('mx_primary_full_rate', 
                                                m3_data, 
                                                mx_data, 
                                                m3_target_finish_time, 
                                                mx_target_finish_time)
      elif (isVehicleAtSecondary(mx_data)):
        start_time = calculateScheduledCharging('mx_secondary_full_rate', 
                                                m3_data, 
                                                mx_data, 
                                                m3_target_finish_time, 
                                                mx_target_finish_time)
      else:
        return None

      total_minutes = (start_time.hour * 60) + start_time.minute

      removeChargeSchedule(MX_VIN, 1)
      addChargeSchedule(MX_VIN, mx_data['response']['drive_state']['latitude'], mx_data['response']['drive_state']['longitude'], total_minutes, 1)
      stopChargeVehicle(MX_VIN) # for some reason charging starts sometimes after scheduled charging API is called

      scheduleBackupCharging(MX_VIN, mx_data, start_time + timedelta(minutes = 10))

      return start_time
    else:
      return None
  except Exception as e:
    logError('scheduleMXCharging():', e)


##
# Schedule charging based on earliest time for off-peak rates.
#
# author: mjhwa@yahoo.com
##
def scheduleEarliestCharging(data, vin): 
  try:
    if (data['response']['charge_state']['charging_state'] != 'Complete' and 
      isVehicleAtPrimary(data) == True):
      start_time = getTomorrowTime(EARLIEST_CHARGING_START_TIME)
      total_minutes = (start_time.hour * 60) + start_time.minute

      # Remove any previous scheduled charging by this program, temporarily set to
      # id=1, until I can figure out how to view the list of charge schedules and
      # their corresponding ID's.
      removeChargeSchedule(vin, 1)
      addChargeSchedule(vin, data['response']['drive_state']['latitude'], data['response']['drive_state']['longitude'], total_minutes, 1)
      stopChargeVehicle(vin) # for some reason charging starts sometimes after scheduled charging API is called

      scheduleBackupCharging(vin, data, start_time + timedelta(minutes = 10))

      return start_time
    else:
      return None
  except Exception as e:
    logErrorStdOut('scheduleEarliestCharging():', e)


##
# Additional scheduled charging check run on crontab.  If it failed to start, this
# will attempt to start it at the target time.
#
# author: mjhwa@yahoo.com
def chargeCheck(vin):
  try:
    data = getVehicleData(vin)

    if (isVehicleAtPrimary(data) and 
        (data['response']['charge_state']['charging_state'] != 'Charging')):
      logInfo('chargeCheck(' + vin + '): Scheduled charging failed to start.  Starting backup charging.')
      startChargeVehicle(vin)
  except Exception as e:
    logError('chargeCheck(' + vin + '):', e)


##
# Schedule vehicle charging based on start time.  Assumes
# the crontab scheduled charging based on finish time has 
# already run and preconditioning does not need to be set 
# again.
#
# author: mjhwa@yahoo.com
##
def chargeEarliest():
  try:
    # get all vehicle data to avoid repeat API calls
    m3_data = getVehicleData(M3_VIN)
    mx_data = getVehicleData(MX_VIN)

    finish_times = calculateFinishTime(m3_data, mx_data)
    m3_finish_time = finish_times['m3_finish_time']
    mx_finish_time = finish_times['mx_finish_time']

    print('Charging at earliest off-peak time')
    print('==================================')
    print('Start time:  12:00 AM')
    print('Model 3 estimated finish time:  ' + m3_finish_time.strftime('%B %d, %Y %H:%M'))
    print('Model X estimated finish time:  ' + mx_finish_time.strftime('%B %d, %Y %H:%M'))
    confirm = input('\nDo you want to override scheduled departure to scheduled start at earliest off-peak time (y/N)?: ')
    if confirm == 'y':
      # set cars for scheduled charging at the earliest off-peak time
      m3_start_time = scheduleEarliestCharging(m3_data, M3_VIN)
      mx_start_time = scheduleEarliestCharging(mx_data, MX_VIN)

      confirm = input('\nDo you want email confirmation (y/N])?: ')
      if confirm == 'y':
        sendScheduledChargeMessage('Model 3',
                                  m3_data,
                                  m3_start_time,
                                  m3_finish_time,
                                  None,
                                  EMAIL_1,
                                  '',
                                  '')
        sendScheduledChargeMessage('Model X',
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
  except Exception as e:
    logErrorStdOut('chargeEarliest():', e)


##
# Create a crontab to check if scheduled charging has started.
#
# author: mjhwa@yahoo.com
##
def scheduleBackupCharging(vin, data, start_time):
  try:
    if (isVehicleAtPrimary(data)):
      # create backup charging start crontab at target time tomorrow
      if (vin == M3_VIN):
        deleteCronTab('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/Charge.py --check=m3 >> /home/pi/tesla/python/cron.log 2>&1')
        createCronTab('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/Charge.py --check=m3 >> /home/pi/tesla/python/cron.log 2>&1', 
                      start_time.month, 
                      start_time.day, 
                      start_time.hour, 
                      start_time.minute)
      elif (vin == MX_VIN):
        deleteCronTab('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/Charge.py --check=mx >> /home/pi/tesla/python/cron.log 2>&1')
        createCronTab('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/Charge.py --check=mx >> /home/pi/tesla/python/cron.log 2>&1', 
                      start_time.month, 
                      start_time.day, 
                      start_time.hour, 
                      start_time.minute)
  except Exception as e:
    logError('scheduleBackupCharging(' + vin + '):', e)


##
# Calculates the scheduled charging time for 2 vehicles depending
# on their location, charge state, and finish time.
#
# author: mjhwa@yahoo.com
##
def calculateScheduledCharging(scenario, m3_data, mx_data, m3_target_finish_time, mx_target_finish_time):
  try:
    miles_needed = calculateMilesNeeded(m3_data, mx_data)
    mx_miles_needed = miles_needed['mx_miles_needed']
    m3_miles_needed = miles_needed['m3_miles_needed']

    # Calculate scheduled charging time based on location of cars
    if ((scenario == 'mx_primary_shared_charging') or (scenario == 'm3_primary_shared_charging')):
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
        if ((mx_target_finish_time != m3_target_finish_time) and (
                  ((mx_start_time_at_full_rate < m3_start_time_at_full_rate) and (mx_target_finish_time > m3_target_finish_time)) or
                  ((m3_start_time_at_full_rate < mx_start_time_at_full_rate) and (m3_target_finish_time > mx_target_finish_time))
                )
           ):
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
  except Exception as e:
    logError('calcuateScheduledCharging(' + scenario + '):', e)


##
# Calculates the finish time based on earlist off-peak start time.
#
# author: mjhwa@yahoo.com
##
def calculateFinishTime(m3_data, mx_data):
  try:
    miles_needed = calculateMilesNeeded(m3_data, mx_data)

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

    mx_finish_time = getTomorrowTime(EARLIEST_CHARGING_START_TIME) + timedelta(hours = mx_charging_time)
    m3_finish_time = getTomorrowTime(EARLIEST_CHARGING_START_TIME) + timedelta(hours = m3_charging_time)

    finish_times = {
        "mx_finish_time": mx_finish_time,
        "m3_finish_time": m3_finish_time
    }
    return finish_times
  except Exception as e:
    logErrorStdOut('calculateFinishTime():', e)


##
# Calculate how many miles are needed for charging based on 
# current range and charging % target.
#
# author: mjhwa@yahoo.com
##
def calculateMilesNeeded(m3_data, mx_data):
  try:
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
        "mx_miles_needed": mx_miles_needed,
        "m3_miles_needed": m3_miles_needed
    }
    return miles_needed
  except Exception as e:
    logError('calculateMilesNeeded():', e)


def sendPluggedInMessage(vehicle, battery_level, battery_range, charge_port_door_open, notify, to, cc, bcc):
  # check if email notification is set to "on" first 
  if (notify == 'on'):
    # send an email if the charge port door is not open, i.e. not plugged in
    if (charge_port_door_open == False):
      message = ('Your car is not plugged in.  \n\nCurrent battery level is '
                  + str(battery_level) 
                  + '%, '
                  + str(battery_range) 
                  + ' estimated miles.  \n\n-Your ' + vehicle)
      sendEmail('Please Plug In Your ' + vehicle, 
                message, 
                to,
                cc,
                bcc, 
                '')
      #print('send email: ' + message)


def sendScheduledChargeMessage(vehicle, data, charge_start_time, finish_time, climate_start_time, to, cc, bcc):
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

    sendEmail(subject, 
              message, 
              to,
              cc,
              bcc, 
              '')


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
def notifyIsTeslaPluggedIn():
  try:
    # get all vehicle data to avoid repeat API calls
    m3_data = getVehicleData(M3_VIN)
    mx_data = getVehicleData(MX_VIN)

    try:
      # get charging configuration info
      service = getGoogleSheetService()
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
      logErrorRetry('Get configuration info from Google Sheets: ' + str(e))
      time.sleep(WAIT_TIME)
      notifyIsTeslaPluggedIn()


    # send email notification if the car is not plugged in
    charge_port_door_open = m3_data['response']['charge_state']['charge_port_door_open']
    battery_level = m3_data['response']['charge_state']['battery_level']
    battery_range = m3_data['response']['charge_state']['battery_range']
    sendPluggedInMessage('Model 3', 
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
    sendPluggedInMessage('Model X', 
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
    m3_target_finish_time = getTomorrowTime(charge_config[dow_index[0]][1])
    mx_target_finish_time = getTomorrowTime(charge_config[dow_index[0]][2])
    m3_charge_start_time = scheduleM3Charging(m3_data, mx_data, m3_target_finish_time, mx_target_finish_time)
    mx_charge_start_time = scheduleMXCharging(m3_data, mx_data, m3_target_finish_time, mx_target_finish_time)

    # set cabin preconditioning the next morning and check that it's not 
    # "skip"
    m3_climate_start_time = None
    mx_climate_start_time = None
    dow_index = [index for index, element in enumerate(climate_config) if day_of_week in element]
    if (climate_config[dow_index[0]][8] != 'skip'):
      m3_climate_start_time = getTomorrowTime(climate_config[dow_index[0]][8])
      m3_climate_start_time = setM3Precondition(m3_data, climate_config[19][1], m3_climate_start_time)
    if (climate_config[dow_index[0]][14] != 'skip'):
      mx_climate_start_time = getTomorrowTime(climate_config[dow_index[0]][14])
      mx_climate_start_time = setMXPrecondition(mx_data, climate_config[19][10], mx_climate_start_time)

    # send email notification if either charging or preconditioning is scheduled
    sendScheduledChargeMessage('Model 3',
                               m3_data,
                               m3_charge_start_time,
                               m3_target_finish_time,
                               m3_climate_start_time,
                               EMAIL_1,
                               '',
                               '')
    sendScheduledChargeMessage('Model X',
                               mx_data,
                               mx_charge_start_time,
                               mx_target_finish_time,
                               mx_climate_start_time,
                               EMAIL_1,
                               '',
                               '')
  except Exception as e:
    logError('notifyIsTeslaPluggedIn():', e)


def printHelp():
  print('Usage: python Charge.py [OPTION...]')
  print('')
  print('--help                 prints the usage and options')
  print('--notify               checks if vehicles are plugged in, ')
  print('                         schedules charging and preconditioning')
  print('--check=m3|mx          backup charging for each vehicle')
  print('--earliest             schedule charging at 12:00 AM')


def main():
  args = sys.argv[1:]
  options = ''
  long_options = ['help', 'notify', 'check=', 'earliest']

  try:
    arguments, values = getopt.getopt(args, options, long_options)

    if len(arguments) < 1: printHelp()

    for currentArg, currentVal in arguments:
      if currentArg in ('--help'):
        printHelp()
      elif currentArg in ('--notify'):
        notifyIsTeslaPluggedIn()
      elif currentArg in ('--check'):
        if currentVal == 'm3':
          chargeCheck(M3_VIN)
        elif currentVal == 'mx':
          chargeCheck(MX_VIN)
        else:
          printHelp()
      elif currentArg in ('--earliest'):
        chargeEarliest()
  except getopt.error as e:
    printHelp()


if __name__ == "__main__":
  main()