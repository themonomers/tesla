import json
import time

from TeslaVehicleAPI import *
from GoogleAPI import *
from Logger import *
from datetime import timedelta, datetime
from crontab import CronTab

OPENWEATHERMAP_KEY = '';
M3_VIN = ''
MX_VIN = ''
WAIT_TIME = 30
TEST_EV_SPREADSHEET_ID = ''

##
# Creates a trigger to precondition the cabin for the following morning, based
# on if the car is at home or if "Eco Mode" is off similar to how Nest
# thermostats work for vacation scenarios.
#
# author: mjhwa@yahoo.com
##
def setM3Precondition(data):
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
      estimated_start_time = datetime(tomorrow_date.year, tomorrow_date.month, tomorrow_date.day, start_time.hour, start_time.minute)

      # create precondition start trigger
      deleteCronTab('/home/pi/tesla/PreconditionM3Start.py')
      createCronTab('/home/pi/tesla/PreconditionM3Start.py', estimated_charge_start_time.hour, estimated_charge_start_time.minute)
  service.close()
  
def setMXPrecondition(data):
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
      estimated_start_time = datetime(tomorrow_date.year, tomorrow_date.month, tomorrow_date.day, start_time.hour, start_time.minute)

      # create precondition start trigger
      deleteCronTab('/home/pi/tesla/PreconditionMXStart.py')
      createCronTab('/home/pi/tesla/PreconditionMXStart.py', estimated_charge_start_time.hour, estimated_charge_start_time.minute)
  service.close()

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
def preconditionM3Start():
  try:
    # check if eco mode is off first so we don't have to even call the Tesla API if we don't have to
    service = getGoogleSheetService()
    eco_mode = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!B24').execute().get('values', [])[0][0]

    if (eco_mode == 'on'): return

    # get local weather
    wdata = getWeather('')

    # get data
    cold_temp_threshold = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!B22').execute().get('values', [])[0][0]
    hot_temp_threshold = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!B23').execute().get('values', [])[0][0]

    # get today's day of week to compare against Google Sheet temp preferences for that day
    day_of_week = datetime.today().day
    seats = []

    # compare temp readings and threshold to determine heating or cooling temps to use
    if (wdata['main']['temp'] < cold_temp_threshold):
      # get pre-heat preferences
      if (day_of_week == 0):  # Sunday
        d_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!B9').execute().get('values', [])[0][0]
        p_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!C9').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return
        
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!D9').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!E9').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!F9').execute().get('values', [])[0][0])
        seats.append(-1) # skip index 3 as it's not assigned in the API
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!G9').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!H9').execute().get('values', [])[0][0])
      elif (day_of_week == 1): # Monday
        d_temp = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!B3').execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!C3').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return

        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!D3').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!E3').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!F3').execute().get('values', [])[0][0])
        seats.append(-1) # skip index 3 as it's not assigned in the API
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!G3').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!H3').execute().get('values', [])[0][0])
      elif (day_of_week == 2): # Tuesday
        d_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!B4').execute().get('values', [])[0][0]
        p_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!C4').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return

        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!D4').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!E4').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!F4').execute().get('values', [])[0][0])
        seats.append(-1) # skip index 3 as it's not assigned in the API
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!G4').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!H4').execute().get('values', [])[0][0])
      elif (day_of_week == 3): # Wednesday
        d_temp = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!B5').execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!C5').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return
        
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!D5').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!E5').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!F5').execute().get('values', [])[0][0])
        seats.append(-1) # skip index 3 as it's not assigned in the API
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!G5').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!H5').execute().get('values', [])[0][0])
      elif (day_of_week == 4): # Thursday
        d_temp = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!B6').execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!C6').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return

        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!D6').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!E6').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!F6').execute().get('values', [])[0][0])
        seats.append(-1) # skip index 3 as it's not assigned in the API
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!G6').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!H6').execute().get('values', [])[0][0])
      elif (day_of_week == 5): # Friday
        d_temp = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!B7').execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!C7').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return
        
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!D7').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!E7').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!F7').execute().get('values', [])[0][0])
        seats.append(-1) # skip index 3 as it's not assigned in the API
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!G7').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!H7').execute().get('values', [])[0][0])
      elif (day_of_week == 6): # Saturday
        d_temp = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!B8').execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!C8').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return

        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!D8').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!E8').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!F8').execute().get('values', [])[0][0])
        seats.append(-1) # skip index 3 as it's not assigned in the API
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!G8').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!H8').execute().get('values', [])[0][0])
      else:
        return
    elif (wdata['main']['temp'] > hot_temp_threshold):
      # get pre-cool preferences
      if (day_of_week == 0): # Sunday
        d_temp = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!B18').execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!C18').execute().get('values', [])[0][0]
        
        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return

        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!D18').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!E18').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!F18').execute().get('values', [])[0][0])
        seats.append(-1) # skip index 3 as it's not assigned in the API
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!G18').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!H18').execute().get('values', [])[0][0])
      elif (day_of_week == 1): # Monday
        d_temp = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!B12').execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!C12').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return

        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!D12').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!E12').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!F12').execute().get('values', [])[0][0])
        seats.append(-1) # skip index 3 as it's not assigned in the API
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!G12').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!H12').execute().get('values', [])[0][0])
      elif (day_of_week == 2): # Tuesday
        d_temp = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!B13').execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!C13').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return
        
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!D13').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!E13').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!F13').execute().get('values', [])[0][0])
        seats.append(-1) # skip index 3 as it's not assigned in the API
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!G13').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!H13').execute().get('values', [])[0][0])
      elif (day_of_week == 3): # Wednesday
        d_temp = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!B14').execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!C14').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return

        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!D14').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!E14').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!F14').execute().get('values', [])[0][0])
        seats.append(-1) # skip index 3 as it's not assigned in the API
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!G14').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!H14').execute().get('values', [])[0][0])
      elif (day_of_week == 4): # Thursday
        d_temp = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!B15').execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!C15').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return
        
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!D15').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!E15').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!F15').execute().get('values', [])[0][0])
        seats.append(-1) # skip index 3 as it's not assigned in the API
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!G15').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!H15').execute().get('values', [])[0][0])
      elif (day_of_week == 5): # Friday
        d_temp = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!B16').execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!C16').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return

        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!D16').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!E16').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!F16').execute().get('values', [])[0][0])
        seats.append(-1) # skip index 3 as it's not assigned in the API
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!G16').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!H16').execute().get('values', [])[0][0])
      elif (day_of_week == 6): # Saturday
        d_temp = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!B17').execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!C17').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return
        
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!D17').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!E17').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!F17').execute().get('values', [])[0][0])
        seats.append(-1) # skip index 3 as it's not assigned in the API
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!G17').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!H17').execute().get('values', [])[0][0])
      else:
        return
    else:
      return # outside temp is within cold and hot thresholds so no preconditioning required; inside and outside car temp readings seem to be inaccurate until the HVAC runs

    # no need to execute if unsure where the car is or if it's in motion
    data = getVehicleData(M3_VIN)
    if (isVehicleAtHome(data)):
      # send command to start auto conditioning
      preconditionCarStart(M3_VIN)

      # set driver and passenger temps
      setCarTemp(M3_VIN, d_temp, p_temp)

      # set seat heater settings
      for index, item in enumerate(seats)
        if (index == 3):
          continue # skip index 3 as it's not assigned in the API
        setCarSeatHeating(M3_VIN, index, item)

      # get stop time preferences
      stop_time = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!B21').execute().get('values', [])[0][0]

      # specific date/time to create a trigger at the preferred stop time (this doesn't seem to work outside of AM, might need refactoring)
      estimated_stop_time = datetime(datetime.today().year, datetime.today().month, datetime.today().day, stop_time.hour, stop_time.minute)
      
      # create trigger to stop preconditioning
      deleteCronTab('/home/pi/tesla/PreconditionM3Stop.py')
      createCronTab('/home/pi/tesla/PreconditionM3Stop.py', estimated_charge_stop_time.hour, estimated_charge_stop_time.minute)
    service.close()
  except as Exception e:
    logError('preconditionM3Start(): ' + e)
    wakeVehicle(M3_VIN)
    time.sleep(WAIT_TIME)
    preconditionM3Start()

def preconditionMXStart():
  try:
    # check if eco mode is off first so we don't have to even call the Tesla API if we don't have to
    service = getGoogleSheetService()
    eco_mode = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!I24').execute().get('values', [])[0][0]

    if (eco_mode == 'on'): return

    # get local weather
    wdata = getWeather('')

    # get data
    cold_temp_threshold = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!I22').execute().get('values', [])[0][0]
    hot_temp_threshold = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!I23').execute().get('values', [])[0][0]

    # get today's day of week to compare against Google Sheet temp preferences for that day
    day_of_week = datetime.today().day
    seats = []

    # compare temp readings and threshold to determine heating or cooling temps to use
    if (wdata['main']['temp'] < cold_temp_threshold):
      # get pre-heat preferences
      if (day_of_week == 0): # Sunday
        d_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!I9').execute().get('values', [])[0][0]
        p_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!J9').execute().get('values', [])[0][0]
        
        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return

        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!K9').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!L9').execute().get('values', [])[0][0])
      elif (day_of_week == 1): # Monday
        d_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!I3').execute().get('values', [])[0][0]
        p_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!J3').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return

        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!K3').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!L3').execute().get('values', [])[0][0])
      elif (day_of_week == 2): # Tuesday
        d_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!I4').execute().get('values', [])[0][0]
        p_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!J4').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return

        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!K4').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!L4').execute().get('values', [])[0][0])
      elif (day_of_week == 3): # Wednesday
        d_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!I5').execute().get('values', [])[0][0]
        p_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!J5').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return
        
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!K5').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!L5').execute().get('values', [])[0][0])
      elif (day_of_week == 4): # Thursday
        d_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!I6').execute().get('values', [])[0][0]
        p_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!J6').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return

        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!K6').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!L6').execute().get('values', [])[0][0])
      elif (day_of_week == 5): # Friday
        d_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!I7').execute().get('values', [])[0][0]
        p_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!J7').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return

        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!K7').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!L7').execute().get('values', [])[0][0])
      elif (day_of_week == 6): # Saturday
        d_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!I8').execute().get('values', [])[0][0]
        p_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!J8').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return
        
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!K8').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!L8').execute().get('values', [])[0][0])
      else:
        return
    elif (wdata['main']['temp'] > hot_temp_threshold):
      # get pre-cool preferences
      if (day_of_week == 0): # Sunday
        d_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!I18').execute().get('values', [])[0][0]
        p_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!J18').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return

        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!K18').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!L18').execute().get('values', [])[0][0])
      elif (day_of_week == 1): # Monday
        d_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!I12').execute().get('values', [])[0][0]
        p_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!J12').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return

        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!K12').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!L12').execute().get('values', [])[0][0])
      elif (day_of_week == 2): # Tuesday
        d_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!I13').execute().get('values', [])[0][0]
        p_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!J13').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return
        
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!K13').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!L13').execute().get('values', [])[0][0])
      elif (day_of_week == 3): # Wednesday
        d_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!I14').execute().get('values', [])[0][0]
        p_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!J14').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return

        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!K14').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!L14').execute().get('values', [])[0][0])
      elif (day_of_week == 4): # Thursday
        d_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!I15').execute().get('values', [])[0][0]
        p_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!J15').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return

        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!K15').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!L15').execute().get('values', [])[0][0])
      elif (day_of_week == 5): # Friday
        d_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!I16').execute().get('values', [])[0][0]
        d_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!J16').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return
        
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!K16').execute().get('values', [])[0][0])
        seats.append(service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!L16').execute().get('values', [])[0][0])
      elif (day_of_week == 6): # Saturday
        d_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!I17').execute().get('values', [])[0][0]
        p_temp = = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!J17').execute().get('values', [])[0][0]

        if ((d_temp.isnumeric() == False) or (p_temp.isnumeric() == False)): return

        seats.push(Number(Sheets.Spreadsheets.Values.get(EV_SPREADSHEET_ID, 'Smart Climate!K17').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(EV_SPREADSHEET_ID, 'Smart Climate!L17').values[0]));
      else:
        return
    else:
      return # outside temp is within cold and hot thresholds so no preconditioning required; inside and outside car temp readings seem to be inaccurate until the HVAC runs

    # no need to execute if unsure where the car is or if it's in motion
    data = getVehicleData(MX_VIN)
    if (isVehicleAtHome(data)):
      # set driver and passenger temps
      setCarTemp(MX_VIN, d_temp, p_temp)

      # send command to start auto conditioning
      preconditionCarStart(MX_VIN)

      # set seat heater settings
      for index, item in enumerate(seats)
        setCarSeatHeating(MX_VIN, index, item)

      # get stop time preferences
      stop_time = service.spreadsheets().values().get(spreadsheetId=TEST_EV_SPREADSHEET_ID, range='Smart Climate!I21').execute().get('values', [])[0][0]
      
      # specific date/time to create a trigger at the preferred stop time (this doesn't seem to work outside of AM, might need refactoring)
      estimated_stop_time = datetime(datetime.today().year, datetime.today().month, datetime.today().day, stop_time.hour, stop_time.minute)

      # create trigger to stop preconditioning
      deleteCronTab('/home/pi/tesla/PreconditionMXStop.py')
      createCronTab('/home/pi/tesla/PreconditionMXStop.py', estimated_charge_stop_time.hour, estimated_charge_stop_time.minute)
    service.close()
  except Exception as e:
    logError('preconditionMXStart(): ' + e)
    wakeVehicle(MX_VIN)
    time.sleep(WAIT_TIME)
    preconditionMXStart();

def preconditionM3Stop():
  try:
    data = getVehicleData(M3_VIN)
    if (isVehicleAtHome(data)): # no need to execute if unsure where the car is or if it's in motion
      preconditionCarStop(M3_VIN)
  except Exception as e:
    logError('preconditionM3Stop(): ' + e)
    wakeVehicle(M3_VIN)
    time.sleep(WAIT_TIME)
    preconditionM3Stop()

def preconditionMXStop():
  try:
    data = getVehicleData(MX_VIN)
    if (isVehicleAtHome(data)): # no need to execute if unsure where the car is or if it's in motion
      preconditionCarStop(MX_VIN)
  except Exception as e:
    logError('preconditionMXStop(): ' + e)
    wakeVehicle(MX_VIN)
    time.sleep(WAIT_TIME)
    preconditionMXStop()

def getWeather(zipcode):
  url =  'https://api.openweathermap.org/data/2.5/weather'
  url += '?zip=' + zipcode
  url += '&APPID=' + OPENWEATHERMAP_KEY
  url += '&units=metric'

  response = requests.get(url)

  return json.loads(response.text)
