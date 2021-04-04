import time
import configparser

from TeslaVehicleAPI import *
from GoogleAPI import *
from Utilities import *
from SmartClimate import getM3SeatSetting
from Logger import *
from datetime import timedelta, datetime

config = configparser.ConfigParser()
config.sections()
config.read('config.ini')
M3_VIN = config['vehicle']['m3_vin']
EV_SPREADSHEET_ID = config['google']['ev_spreadsheet_id'] 
ZIPCODE = config['weather']['zipcode']

WAIT_TIME = 30 


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
def main():
  try:
    # check if eco mode is off first so we don't have to even call the Tesla API if we don't have to
    service = getGoogleSheetService()
    eco_mode = service.spreadsheets().values().get(
      spreadsheetId=EV_SPREADSHEET_ID, 
      range='Smart Climate!B24'
    ).execute().get('values', [])[0][0]

    if (eco_mode == 'on'): return
    
    # get local weather
    wdata = getWeather(ZIPCODE)
    #print('temp: ' + str(wdata['main']['temp']))
    
    # get data
    cold_temp_threshold = service.spreadsheets().values().get(
      spreadsheetId=EV_SPREADSHEET_ID, 
      range='Smart Climate!B22'
    ).execute().get('values', [])[0][0]
    hot_temp_threshold = service.spreadsheets().values().get(
      spreadsheetId=EV_SPREADSHEET_ID, 
      range='Smart Climate!B23'
    ).execute().get('values', [])[0][0]
    #print('cold temp threshold: ' + cold_temp_threshold)
    #print('hot temp threshold: ' + hot_temp_threshold)
      
    # get today's day of week to compare against Google Sheet temp preferences 
    # for that day
    day_of_week = datetime.today().weekday()
    seats = []
    
    # compare temp readings and threshold to determine heating or cooling temps 
    # to use
    if (wdata['main']['temp'] < cold_temp_threshold):
      # get pre-heat preferences  
      if (day_of_week == 6):  # Sunday
        try:
          d_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!B9'
          ).execute().get('values', [])[0][0])
          p_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!C9'
          ).execute().get('values', [])[0][0])
        except ValueError:
         return

        seats = getM3SeatSetting(
          seats,
          'Smart Climate!D9',
          'Smart Climate!E9',
          'Smart Climate!F9',
          'Smart Climate!G9',
          'Smart Climate!H9'
        )
      elif (day_of_week == 0): # Monday
        try:
          d_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!B3'
          ).execute().get('values', [])[0][0])
          p_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!C3'
          ).execute().get('values', [])[0][0])
        except ValueError:
         return

        seats = getM3SeatSetting(
          seats,
          'Smart Climate!D3',
          'Smart Climate!E3',
          'Smart Climate!F3',
          'Smart Climate!G3',
          'Smart Climate!H3'
        )
      elif (day_of_week == 1): # Tuesday
        try:
          d_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!B4'
          ).execute().get('values', [])[0][0])
          p_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!C4'
          ).execute().get('values', [])[0][0])
        except ValueError:
         return

        seats = getM3SeatSetting(
          seats,
          'Smart Climate!D4',
          'Smart Climate!E4',
          'Smart Climate!F4',
          'Smart Climate!G4',
          'Smart Climate!H4'
        )
      elif (day_of_week == 2): # Wednesday
        try:
          d_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!B5'
          ).execute().get('values', [])[0][0])
          p_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!C5'
          ).execute().get('values', [])[0][0])
        except ValueError:
         return

        seats = getM3SeatSetting(
          seats,
          'Smart Climate!D5',
          'Smart Climate!E5',
          'Smart Climate!F5',
          'Smart Climate!G5',
          'Smart Climate!H5'
        )
      elif (day_of_week == 3): # Thursday
        try:
          d_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!B6'
          ).execute().get('values', [])[0][0])
          p_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!C6'
          ).execute().get('values', [])[0][0])
        except ValueError:
         return

        seats = getM3SeatSetting(
          seats,
          'Smart Climate!D6',
          'Smart Climate!E6',
          'Smart Climate!F6',
          'Smart Climate!G6',
          'Smart Climate!H6'
        )
      elif (day_of_week == 4): # Friday
        try:
          d_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!B7'
          ).execute().get('values', [])[0][0])
          p_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!C7'
          ).execute().get('values', [])[0][0])
        except ValueError:
         return

        seats = getM3SeatSetting(
          seats,
          'Smart Climate!D7',
          'Smart Climate!E7',
          'Smart Climate!F7',
          'Smart Climate!G7',
          'Smart Climate!H7'
        )
      elif (day_of_week == 5): # Saturday
        try:
          d_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!B8'
          ).execute().get('values', [])[0][0])
          p_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!C8'
          ).execute().get('values', [])[0][0])
        except ValueError:
         return

        seats = getM3SeatSetting(
          seats,
          'Smart Climate!D8',
          'Smart Climate!E8',
          'Smart Climate!F8',
          'Smart Climate!G8',
          'Smart Climate!H8'
        )
      else:
        return
    elif (wdata['main']['temp'] > hot_temp_threshold):
      # get pre-cool preferences
      if (day_of_week == 6): # Sunday
        try:
          d_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!B18'
          ).execute().get('values', [])[0][0])
          p_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!C18'
          ).execute().get('values', [])[0][0])
        except ValueError:
         return

        seats = getM3SeatSetting(
          seats,
          'Smart Climate!D18',
          'Smart Climate!E18',
          'Smart Climate!F18',
          'Smart Climate!G18',
          'Smart Climate!H18'
        )        
      elif (day_of_week == 0): # Monday
        try:
          d_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!B12'
          ).execute().get('values', [])[0][0])
          p_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!C12'
          ).execute().get('values', [])[0][0])
        except ValueError:
         return

        seats = getM3SeatSetting(
          seats,
          'Smart Climate!D12',
          'Smart Climate!E12',
          'Smart Climate!F12',
          'Smart Climate!G12',
          'Smart Climate!H12'
        )          
      elif (day_of_week == 1): # Tuesday
        try:
          d_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!B13'
          ).execute().get('values', [])[0][0])
          p_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!C13'
          ).execute().get('values', [])[0][0])
        except ValueError:
         return

        seats = getM3SeatSetting(
          seats,
          'Smart Climate!D13',
          'Smart Climate!E13',
          'Smart Climate!F13',
          'Smart Climate!G13',
          'Smart Climate!H13'
        )          
      elif (day_of_week == 2): # Wednesday
        try:
          d_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!B14'
          ).execute().get('values', [])[0][0])
          p_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!C14'
          ).execute().get('values', [])[0][0])
        except ValueError:
         return

        seats = getM3SeatSetting(
          seats,
          'Smart Climate!D14',
          'Smart Climate!E14',
          'Smart Climate!F14',
          'Smart Climate!G14',
          'Smart Climate!H14'
        )          
      elif (day_of_week == 3): # Thursday
        try:
          d_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!B15'
          ).execute().get('values', [])[0][0])
          p_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!C15'
          ).execute().get('values', [])[0][0])
        except ValueError:
         return

        seats = getM3SeatSetting(
          seats,
          'Smart Climate!D15',
          'Smart Climate!E15',
          'Smart Climate!F15',
          'Smart Climate!G15',
          'Smart Climate!H15'
        )          
      elif (day_of_week == 4): # Friday
        try:
          d_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!B16'
          ).execute().get('values', [])[0][0])
          p_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!C16'
          ).execute().get('values', [])[0][0])
        except ValueError:
         return

        seats = getM3SeatSetting(
          seats,
          'Smart Climate!D16',
          'Smart Climate!E16',
          'Smart Climate!F16',
          'Smart Climate!G16',
          'Smart Climate!H16'
        )          
      elif (day_of_week == 5): # Saturday
        try:
          d_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!B17'
          ).execute().get('values', [])[0][0])
          p_temp = float(service.spreadsheets().values().get(
            spreadsheetId=EV_SPREADSHEET_ID, 
            range='Smart Climate!C17'
          ).execute().get('values', [])[0][0])
        except ValueError:
         return

        seats = getM3SeatSetting(
          seats,
          'Smart Climate!D17',
          'Smart Climate!E17',
          'Smart Climate!F17',
          'Smart Climate!G17',
          'Smart Climate!H17'
        )  
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
      for index, item in enumerate(seats):
        if (index == 3):
          continue # skip index 3 as it's not assigned in the API
        setCarSeatHeating(M3_VIN, index, item)

      # get stop time preferences
      stop_time = service.spreadsheets().values().get(
        spreadsheetId=EV_SPREADSHEET_ID, 
        range='Smart Climate!B21'
      ).execute().get('values', [])[0][0]
      
      # specific date/time to create a crontab at the preferred stop time 
      # (this doesn't seem to work outside of AM, might need refactoring)
      stop_time = datetime.strptime(stop_time, '%I:%M %p').time() 
      estimated_stop_time = datetime(
        datetime.today().year, 
        datetime.today().month, 
        datetime.today().day, 
        stop_time.hour, 
        stop_time.minute
      )
      
      # create crontab to stop preconditioning
      deleteCronTab('/home/pi/tesla/python/PreconditionM3Stop.py')
      createCronTab(
        '/home/pi/tesla/python/PreconditionM3Stop.py', 
        estimated_stop_time.month, 
        estimated_stop_time.day, 
        estimated_stop_time.hour, 
        estimated_stop_time.minute
      )
    service.close()
  except Exception as e:
    logError('preconditionM3Start(): ' + str(e))
    wakeVehicle(M3_VIN)
    time.sleep(WAIT_TIME)
    main()

if __name__ == "__main__":
  main()

