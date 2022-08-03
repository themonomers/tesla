from GoogleAPI import getGoogleSheetService
from Utilities import isVehicleAtHome, deleteCronTab, createCronTab, getConfig
from Logger import logError
from datetime import timedelta, datetime

EV_SPREADSHEET_ID = getConfig()['google']['ev_spreadsheet_id']


##
# Creates a trigger to precondition the cabin for the following morning, 
# based on if the car is at home and if "Eco Mode" is off similar to how 
# Nest thermostats work for vacation scenarios.  With the new endpoints 
# released, you can achieve the same functionality by setting scheduled 
# departure for preconditioning.  I decided to keep this code running 
# as I don't drive long distances so the added feature of preconditioning 
# the battery, in addition to the cabin, is a waste of energy (entropy) 
# for me.
#
# author: mjhwa@yahoo.com
## 
def setM3Precondition(data):
  try: 
    service = getGoogleSheetService()
    eco_mode = service.spreadsheets().values().get(
      spreadsheetId=EV_SPREADSHEET_ID, 
      range='Smart Climate!B24'
    ).execute().get('values', [])[0][0]
    
    # check if eco mode is off first so we don't have to even call the 
    # Tesla API if we don't have to
    if (eco_mode == 'off'):
      # check if the car is with 0.25 miles of home
      if (isVehicleAtHome(data)):
        # get start time preferences
        start_time = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!B20'
        ).execute().get('values', [])[0][0]
      
        # specific date/time to create a crontab for tomorrow morning at 
        # the preferred start time
        tomorrow_date = datetime.today() + timedelta(1)
        start_time = datetime.strptime(start_time, '%I:%M %p').time()
        estimated_start_time = datetime(
          tomorrow_date.year, 
          tomorrow_date.month, 
          tomorrow_date.day, 
          start_time.hour, 
          start_time.minute
        )
      
        # create precondition start crontab
        deleteCronTab('python /home/pi/tesla/python/PreconditionM3Start.py')
        createCronTab('python /home/pi/tesla/python/PreconditionM3Start.py', 
                      estimated_start_time.month, 
                      estimated_start_time.day, 
                      estimated_start_time.hour, 
                      estimated_start_time.minute)
    service.close()
  except Exception as e:
    logError('setM3Precondition(): ' + str(e))


def setMXPrecondition(data):
  try: 
    service = getGoogleSheetService()
    eco_mode = service.spreadsheets().values().get(
      spreadsheetId=EV_SPREADSHEET_ID, 
      range='Smart Climate!I24'
    ).execute().get('values', [])[0][0]
  
    # check if eco mode is off first so we don't have to even call the 
    # Tesla API if we don't have to
    if (eco_mode == 'off'):
      # check if the car is with 0.25 miles of home
      if (isVehicleAtHome(data)):
        # get start time preferences
        start_time = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!I20'
        ).execute().get('values', [])[0][0]
      
        # specific date/time to create a crontab for tomorrow morning at 
        # the preferred start time
        tomorrow_date = datetime.today() + timedelta(1)
        start_time = datetime.strptime(start_time, '%I:%M %p').time()
        estimated_start_time = datetime(
          tomorrow_date.year, 
          tomorrow_date.month, 
          tomorrow_date.day, 
          start_time.hour, 
          start_time.minute
        )
      
        # create precondition start crontab
        deleteCronTab('python /home/pi/tesla/python/PreconditionMXStart.py')
        createCronTab('python /home/pi/tesla/python/PreconditionMXStart.py', 
                      estimated_start_time.month, 
                      estimated_start_time.day, 
                      estimated_start_time.hour, 
                      estimated_start_time.minute)
    service.close()
  except Exception as e:
    logError('setMXPrecondition(): ' + str(e))

##
# Helper function to reduce lines of repetitive code to retrieve seat heater 
# settings in Google Sheet.
#
# author: mjhwa@yahoo.com
##
def getM3SeatSetting(data, s1, s2, s3, s5, s6):
  try:
    service = getGoogleSheetService()

    data.append(
      service.spreadsheets().values().get(
        spreadsheetId=EV_SPREADSHEET_ID, 
        range=s1
      ).execute().get('values', [])[0][0]
    )
    data.append(
      service.spreadsheets().values().get(
        spreadsheetId=EV_SPREADSHEET_ID, 
        range=s2
      ).execute().get('values', [])[0][0]
    )
    data.append(
      service.spreadsheets().values().get(
        spreadsheetId=EV_SPREADSHEET_ID, 
        range=s3
      ).execute().get('values', [])[0][0]
    )
    data.append(-1) # skip index 3 as it's not assigned in the API
    data.append(
      service.spreadsheets().values().get(
        spreadsheetId=EV_SPREADSHEET_ID, 
        range=s5
      ).execute().get('values', [])[0][0]
    )
    data.append(
      service.spreadsheets().values().get(
        spreadsheetId=EV_SPREADSHEET_ID, 
        range=s6
      ).execute().get('values', [])[0][0]
    )

    service.close

    return data
  except Exception as e:
    logError('getM3SeatSetting(): ' + str(e))


def getMXSeatSetting(data, s1, s2):
  try:
    service = getGoogleSheetService()

    data.append(
      service.spreadsheets().values().get(
        spreadsheetId=EV_SPREADSHEET_ID, 
        range=s1
      ).execute().get('values', [])[0][0]
    )
    data.append(
      service.spreadsheets().values().get(
        spreadsheetId=EV_SPREADSHEET_ID, 
        range=s2
      ).execute().get('values', [])[0][0]
    )

    service.close

    return data
  except Exception as e:
    logError('getMXSeatSetting(): ' + str(e))

