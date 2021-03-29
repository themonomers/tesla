import json
import time
import math

from TeslaVehicleAPI import *
from GoogleAPI import *
from SendEmail import *
from Logger import *
from datetime import timedelta, datetime
from crontab import CronTab

M3_VIN = ''
MX_VIN = ''
WAIT_TIME = 30
R = 3958.8;  #Earth radius in miles
HOME_LAT = 
HOME_LNG = 
NAPA_LAT = 
NAPA_LNG = 
TEST_EV_SPREADSHEET_ID = ''

email_address1 = 'mjhwa@yahoo.com'
email_address2 = ''

##
# Writes to a Google Sheet that calculates optimum charging start times for
# 2 vehicles to reach the target SoC by a time specified in the sheet.
#
# author: mjhwa@yahoo.com
##
def writeM3StartTimes(data):
  try:
    inputs = []

    # write m3 range to Google Sheet
    inputs.append({
      'range': 'Smart Charger!B10',
      'values': [[data['response']['charge_state']['battery_range']]]
    })

    # write m3 time and date stamp to Google Sheet
    inputs.append({
      'range': 'Smart Charger!D10',
      'values': [[datetime.today().strftime('%H:%M:%S') + ', ' + datetime.today().strftime('%m/%d/%Y')]]
    })
    
    # write m3 scheduled charge time to Google Sheet
    inputs.append({
      'range': 'Smart Charger!E28',
      'values': [[data['response']['charge_state']['scheduled_charging_start_time']]]
    })

    # write m3 charge limit to Google Sheet
    inputs.append({
      'range': 'Smart Charger!B16',
      'values': [[data['response']['charge_state']['charge_limit_soc']/100.0]]
    })

    # write m3 max range
    inputs.append({
      'range': 'Smart Charger!B6',
      'values': [[data['response']['charge_state']['battery_range']/(data['response']['charge_state']['battery_level']/100.0)]]
    })

    # batch write data to sheet
    service = getGoogleSheetService()
    service.spreadsheets().values().batchUpdate(spreadsheetId=TEST_EV_SPREADSHEET_ID, body={'data': inputs, 'valueInputOption': 'USER_ENTERED'}).execute()
  except Exception as e:
    print('writeM3StartTimes(): ' + str(e))
    logError('writeM3StartTimes(): ' + str(e))
  finally:
    service.close()

def writeMXStartTimes(data):
  try:
    inputs = []

    # write mx range to Google Sheet
    inputs.append({
      'range': 'Smart Charger!B9',
      'values': [[data['response']['charge_state']['battery_range']]]
    })

    # write mx time and date stamp to Google Sheet
    inputs.append({
      'range': 'Smart Charger!D9',
      'values': [[datetime.today().strftime('%H:%M:%S') + ', ' + datetime.today().strftime('%m/%d/%Y')]]
    })
    
    # write mx scheduled charge time to Google Sheet
    inputs.append({
      'range': 'Smart Charger!F28',
      'values': [[data['response']['charge_state']['scheduled_charging_start_time']]]
    })

    # write mx charge limit to Google Sheet
    inputs.append({
      'range': 'Smart Charger!B15',
      'values': [[data['response']['charge_state']['charge_limit_soc']/100.0]]
    })

    # write mx max range
    inputs.append({
      'range': 'Smart Charger!B5',
      'values': [[data['response']['charge_state']['battery_range']/(data['response']['charge_state']['battery_level']/100.0)]]
    })

    # batch write data to sheet
    service = getGoogleSheetService()
    service.spreadsheets().values().batchUpdate(spreadsheetId=TEST_EV_SPREADSHEET_ID, body={'data': inputs, 'valueInputOption': 'USER_ENTERED'}).execute()
  except Exception as e:
    print('writeMXStartTimes(): ' + str(e))
    logError('writeMXStartTimes(): ' + str(e))
  finally:
    service.close()

##
#
#
#
##
def deleteCronTab(command):
  cron = CronTab(user='pi')
  job = cron.find_command(command)
  cron.remove(job)
  cron.write()
  
##
#
#
#
##
def createCronTab(command, hour, minute):
  cron = CronTab(user='pi')
  job = cron.new(command=command)
  job.hour.on(hour)
  job.minute.on(minute)
  cron.write()

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
  d = getDistance(data['response']['drive_state']['latitude'], data['response']['drive_state']['longitude'], lat, lng)

  # check if the car is more than a quarter of a mile away
  if (d < 0.25):
    return True
  else:
    return False

def getDistance(car_lat, car_lng, x_lat, x_lng):
  diff_lat = toRad(car_lat - x_lat)
  diff_lng = toRad(car_lng - x_lng)

  a = (math.sin(diff_lat/2) * math.sin(diff_lat/2)) + math.cos(x_lat) * math.cos(car_lat) * (math.sin(diff_lng/2) * math.sin(diff_lng/2))
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
  d = R * c

  return d

def toRad(x):
  return x * math.pi / 180

##
# Read vehicle range and estimated charge start time from a the Google Sheet,
# then create a crontab to execute at a specific date and time.  The crontab
# will call a function to wake up the vehicle and send a command to start
# charging.
#
# Since there's isn't an API yet to set the vehicle's scheduled charge time,
# this workaround is to set the time as "late" (5a) as possible in the vehicle
# console, then have this function set up a crontab to manually start charging
# the car at the optimal time.  When an API is available to set scheduled charge
# times, this function won't need to be run on a crontab and can be set in the
# car.
#
# author: mjhwa@yahoo.com
##
def scheduleM3Charging(m3_data, mx_data):
  try:
    deleteCronTab('/home/pi/tesla/ChargeM3.py')
    deleteCronTab('/home/pi/tesla/ChargeM3Backup.py')

    service = getGoogleSheetService()

    target_soc = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Charger!B18').execute().get('values', [])[0][0]
    current_soc = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Charger!B10').execute().get('values', [])[0][0]

    # if the target SoC is greater than the current SoC and charging state isn't
    # Complete, create a crontab for charging
    if ((target_soc > current_soc) and (m3_data['response']['charge_state']['charging_state'] != 'Complete')):
      # get calculated start time depending on location of cars
      if ((isVehicleAtHome(m3_data) == True) and (isVehicleAtHome(mx_data) == True)):
        start_time = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Charger!E26').execute().get('values', [])[0][0]
      elif ((isVehicleAtHome(m3_data) == True) and (isVehicleAtHome(mx_data) == False)):
        start_time = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Charger!J25').execute().get('values', [])[0][0]
      elif (isVehicleAtNapa(m3_data)):
        start_time = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Charger!J26').execute().get('values', [])[0][0]
      else:
        return
      
      # set the right date of the estimated charge time based on AM or PM
      if (str(start_time).find('AM') >= 0):
        tomorrow_date = datetime.today() + timedelta(1)
        start_time = datetime.strptime(start_time, '%I:%M %p').time()
        estimated_charge_start_time = datetime(tomorrow_date.year, tomorrow_date.month, tomorrow_date.day, start_time.hour, start_time.minute)
      else:
        start_time = datetime.strptime(start_time, '%I:%M %p').time()
        estimated_charge_start_time = datetime(datetime.today().year, datetime.today().month, datetime.today().day, start_time.hour, start_time.minute)

      # if the estimated start time is after the car's onboard scheduled start
      # time, exit
      # TODO:  Check if it's AM or PM
      car_charge_schedule = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Charger!E27').execute().get('values', [])[0][0]
      tomorrow_date = datetime.today() + timedelta(1)
      car_charge_schedule = datetime.strptime(car_charge_schedule, '%I:%M %p').time()
      car_charge_schedule = datetime(tomorrow_date.year, tomorrow_date.month, tomorrow_date.day, car_charge_schedule.hour, car_charge_schedule.minute)
      service.close()

      if (estimated_charge_start_time > car_charge_schedule):
        return

      # create crontab
      createCronTab('/home/pi/tesla/ChargeM3.py', estimated_charge_start_time.hour, estimated_charge_start_time.minute)

      # send email notification
      message = 'The Model 3 is set to charge on ' + str(estimated_charge_start_time) + '.'
      sendEmail(email_address1, 'Model 3 Set to Charge', message, '')

      # create back up crontab for 15 minutes later
      estimated_backup_charge_start_time = estimated_charge_start_time + timedelta(minutes=15)
      createCronTab('/home/pi/tesla/ChargeM3Backup.py', estimated_backup_charge_start_time.hour, estimated_backup_charge_start_time.minute)
  except Exception as e:
    print('scheduleM3Charging(): ' + str(e))
    logError('scheduleM3Charging(): ' + str(e))
    
def scheduleMXCharging(m3_data, mx_data):
  try:
    deleteCronTab('/home/pi/tesla/ChargeMX.py')
    deleteCronTab('/home/pi/tesla/ChargeMXBackup.py')

    service = getGoogleSheetService()

    target_soc = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Charger!B17').execute().get('values', [])[0][0]
    current_soc = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Charger!B9').execute().get('values', [])[0][0]

    # if the target SoC is greater than the current SoC and charging state isn't
    # Complete, create a crontab for charging
    if ((target_soc > current_soc) and (mx_data['response']['charge_state']['charging_state'] != 'Complete')):
      # get calculated start time depending on location of cars
      if ((isVehicleAtHome(mx_data) == True) and (isVehicleAtHome(m3_data) == True)):
        start_time = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Charger!F26').execute().get('values', [])[0][0]
      elif ((isVehicleAtHome(mx_data) == True) and (isVehicleAtHome(m3_data) == False)):
        start_time = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Charger!K26').execute().get('values', [])[0][0]
      elif (isVehicleAtNapa(mx_data)):
        start_time = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Charger!K25').execute().get('values', [])[0][0]
      else:
        return

      # set the right date of the estimated charge time based on AM or PM
      if (str(start_time).find('AM') >= 0):
        tomorrow_date = datetime.today() + timedelta(1)
        start_time = datetime.strptime(start_time, '%I:%M %p').time()
        estimated_charge_start_time = datetime(tomorrow_date.year, tomorrow_date.month, tomorrow_date.day, start_time.hour, start_time.minute)
      else:
        start_time = datetime.strptime(start_time, '%I:%M %p').time()
        estimated_charge_start_time = datetime(datetime.today().year, datetime.today().month, datetime.today().day, start_time.hour, start_time.minute)
        
      # if the estimated start time is after the car's onboard scheduled start
      # time, exit
      # TODO:  Check if it's AM or PM
      car_charge_schedule = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Charger!F27').execute().get('values', [])[0][0]
      tomorrow_date = datetime.today() + timedelta(1)
      car_charge_schedule = datetime.strptime(car_charge_schedule, '%I:%M %p').time()
      car_charge_schedule = datetime(tomorrow_date.year, tomorrow_date.month, tomorrow_date.day, car_charge_schedule.hour, car_charge_schedule.minute)
      service.close()

      if (estimated_charge_start_time > car_charge_schedule):
        return

      # create crontab
      createCronTab('/home/pi/tesla/ChargeMX.py', estimated_charge_start_time.hour, estimated_charge_start_time.minute)

      # send email notification
      message = 'The Model X is set to charge on ' + str(estimated_charge_start_time) + '.'
      sendEmail(email_address1, 'Model X Set to Charge', message, '')

      # create back up crontab for 15 minutes later
      estimated_backup_charge_start_time = estimated_charge_start_time + timedelta(minutes=15)
      createCronTab('/home/pi/tesla/ChargeMXBackup.py', estimated_backup_charge_start_time.hour, estimated_backup_charge_start_time.minute)
  except Exception as e:
    print('scheduleMXCharging(): ' + str(e))
    logError('scheduleMXCharging(): ' + str(e))

##
# Checks to see if the vehicles are plugged in, inferred from the charge port
# door status, and sends an email to notify if it's not.  Also sets trigger
# to manually start charging at the calculated date and time. Skips if it's
# not within 0.25 miles from home.
#
# If one of the other cars is in Napa, set time charge start time based on the
# alternate charge rate and set the charge start time for the one at home to
# charge at full charge rate.
#
# author: mjhwa@yahoo.com
##
def main():
  try:
    # get all vehicle data to avoid repeat API calls
    m3_data = getVehicleData(M3_VIN)
    mx_data = getVehicleData(MX_VIN)

    # write data to calculate charging start times; both functions for this needs
    # to be executed, because the calculation on the Google Sheet is dependent on
    # values from both vehicles
    writeM3StartTimes(m3_data)
    writeMXStartTimes(mx_data)

    # get car info
    charge_port_door_open = m3_data['response']['charge_state']['charge_port_door_open']
    battery_level = m3_data['response']['charge_state']['battery_level']
    battery_range = m3_data['response']['charge_state']['battery_range']

    service = getGoogleSheetService()
    email_notification = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Charger!H10').execute().get('values', [])

    # check if email notification is set to "on" first
    if (email_notification[0][0] == 'on'):
      # send an email if the charge port door is not open, i.e. not plugged in
      if (charge_port_door_open == False):
        message =  'Your car is not plugged in.  \n\nCurrent battery level is '
        message += str(battery_level) + '%, '
        message += str(battery_range) + ' estimated miles.  \n\n-Your Model 3'
        sendEmail(email_address1, 'Please Plug In Your Model 3', message, '')

    charge_port_door_open = mx_data['response']['charge_state']['charge_port_door_open']
    battery_level = mx_data['response']['charge_state']['battery_level']
    battery_range = mx_data['response']['charge_state']['battery_range']

    email_notification = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Charger!H9').execute().get('values', [])
    service.close()
    
    # check if email notification is set to "on" first
    if (email_notification[0][0] == 'on'):
      # send an email if the charge port door is not open, i.e. not plugged in
      if (charge_port_door_open == False):
        message =  'Your car is not plugged in.  \n\nCurrent battery level is '
        message += str(battery_level) + '%, '
        message += str(battery_range) + ' estimated miles.  \n\n-Your Model X'
        sendEmail(email_address2, 'Please Plug In Your Model X', message, email_address1)
        #print('send email: ' + message)

    # set trigger for charging
    scheduleM3Charging(m3_data, mx_data)
    scheduleMXCharging(m3_data, mx_data)

    # set cabin preconditioning the next morning
    #setM3Precondition(m3_data);
    #setMXPrecondition(mx_data);
  except Exception as e:
    print('notifyIsTeslaPluggedIn(): ' + str(e))
    logError('notifyIsTeslaPluggedIn(): ' + str(e))
    wakeVehicle(M3_VIN)
    wakeVehicle(MX_VIN)
    time.sleep(WAIT_TIME)
    main()

if __name__ == "__main__":
  main()
