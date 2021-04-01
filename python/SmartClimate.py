from TeslaVehicleAPI import *
from GoogleAPI import *
from Utilities import *
from datetime import timedelta, datetime

TEST_EV_SPREADSHEET_ID = ''

##
# Creates a trigger to precondition the cabin for the following morning, based
# on if the car is at home or if "Eco Mode" is off similar to how Nest
# thermostats work for vacation scenarios.
#
# author: mjhwa@yahoo.com
##
def setM3Precondition(data):
  try:
    service = getGoogleSheetService()
    eco_mode = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!B24').execute().get('values', [])[0][0]

    # check if eco mode is off first so we don't have to even call the Tesla API if we don't have to
    if (eco_mode == 'off'):
      # check if the car is with 0.25 miles of home
      if (isVehicleAtHome(data)):
        # get start time preferences
        start_time = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!B20').execute().get('values', [])[0][0]

        # specific date/time to create a trigger for tomorrow morning at the preferred start time
        tomorrow_date = datetime.today() + timedelta(1)
        start_time = datetime.strptime(start_time, '%I:%M %p').time()
        estimated_start_time = datetime(tomorrow_date.year, tomorrow_date.month, tomorrow_date.day, start_time.hour, start_time.minute)

        # create precondition start trigger
        deleteCronTab('/home/pi/tesla/PreconditionM3Start.py')
        createCronTab('/home/pi/tesla/PreconditionM3Start.py', estimated_start_time.hour, estimated_start_time.minute)
    service.close()
  except Exception as e:
    logError('setM3Precondition(): ' + str(e))
  
def setMXPrecondition(data):
  try:
    service = getGoogleSheetService()
    eco_mode = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!I24').execute().get('values', [])[0][0]

    # check if eco mode is off first so we don't have to even call the Tesla API if we don't have to
    if (eco_mode == 'off'):
      # check if the car is with 0.25 miles of home
      if (isVehicleAtHome(data)):
        # get start time preferences
        start_time = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!I20').execute().get('values', [])[0][0]

        # specific date/time to create a trigger for tomorrow morning at the preferred start time
        tomorrow_date = datetime.today() + timedelta(1)
        start_time = datetime.strptime(start_time, '%I:%M %p').time()
        estimated_start_time = datetime(tomorrow_date.year, tomorrow_date.month, tomorrow_date.day, start_time.hour, start_time.minute)

        # create precondition start trigger
        deleteCronTab('/home/pi/tesla/PreconditionMXStart.py')
        createCronTab('/home/pi/tesla/PreconditionMXStart.py', estimated_start_time.hour, estimated_start_time.minute)
    service.close()
  except Exception as e:
    logError('setMXPrecondition(): ' + str(e))
