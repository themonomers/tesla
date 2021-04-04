import time
import configparser

from TeslaVehicleAPI import *
from GoogleAPI import *
from Utilities import *
from SmartClimate import getMXSeatSetting
from Logger import *
from datetime import timedelta, datetime

config = configparser.ConfigParser()
config.sections()
config.read('config.ini')
MX_VIN = config['vehicle']['mx_vin']
EV_SPREADSHEET_ID = config['google']['ev_spreadsheet_id']
ZIPCODE = config['weather']['zipcode']

WAIT_TIME = 30 


def main():
  try:
    # check if eco mode is off first so we don't have to even call the 
    # Tesla API if we don't have to
    service = getGoogleSheetService()
    eco_mode = service.spreadsheets().values().get(
      spreadsheetId=EV_SPREADSHEET_ID, 
      range='Smart Climate!I24'
    ).execute().get('values', [])[0][0]

    if (eco_mode == 'on'): return
    
    # get local weather
    wdata = getWeather(ZIPCODE)
    
    # get data
    cold_temp_threshold = service.spreadsheets().values().get(
      spreadsheetId=EV_SPREADSHEET_ID, 
      range='Smart Climate!I22'
    ).execute().get('values', [])[0][0]
    hot_temp_threshold = service.spreadsheets().values().get(
      spreadsheetId=EV_SPREADSHEET_ID, 
      range='Smart Climate!I23'
    ).execute().get('values', [])[0][0]

    # get today's day of week to compare against Google Sheet temp preferences 
    # for that day
    day_of_week = datetime.today().day
    seats = []
    
    # compare temp readings and threshold to determine heating or cooling temps 
    # to use
    if (wdata['main']['temp'] < cold_temp_threshold):
      # get pre-heat preferences
      if (day_of_week == 0): # Sunday
        d_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!I9'
        ).execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!J9'
        ).execute().get('values', [])[0][0]

        if (
          (d_temp.isnumeric() == False) 
          or (p_temp.isnumeric() == False)
        ): return
        
        seats = getMXSeatSetting(
          seats,
          'Smart Climate!K9',
          'Smart Climate!L9'
        )
      elif (day_of_week == 1): # Monday
        d_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!I3'
        ).execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!J3'
        ).execute().get('values', [])[0][0]

        if (
          (d_temp.isnumeric() == False) 
          or (p_temp.isnumeric() == False)
        ): return

        seats = getMXSeatSetting(
          seats,
          'Smart Climate!K3',
          'Smart Climate!L3' 
        )        
      elif (day_of_week == 2): # Tuesday
        d_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!I4'
        ).execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!J4'
        ).execute().get('values', [])[0][0]

        if (
          (d_temp.isnumeric() == False) 
          or (p_temp.isnumeric() == False)
        ): return

        seats = getMXSeatSetting(
          seats,
          'Smart Climate!K4',
          'Smart Climate!L4' 
        )        
      elif (day_of_week == 3): # Wednesday
        d_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!I5'
        ).execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!J5'
        ).execute().get('values', [])[0][0]
        
        if (
          (d_temp.isnumeric() == False) 
          or (p_temp.isnumeric() == False)
        ): return

        seats = getMXSeatSetting(
          seats,
          'Smart Climate!K5',
          'Smart Climate!L5' 
        )        
      elif (day_of_week == 4): # Thursday
        d_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!I6'
        ).execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!J6'
        ).execute().get('values', [])[0][0]

        if (
          (d_temp.isnumeric() == False) 
          or (p_temp.isnumeric() == False)
        ): return

        seats = getMXSeatSetting(
          seats,
          'Smart Climate!K6',
          'Smart Climate!L6' 
        )        
      elif (day_of_week == 5): # Friday
        d_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!I7'
        ).execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!J7'
        ).execute().get('values', [])[0][0]
        
        if (
          (d_temp.isnumeric() == False) 
          or (p_temp.isnumeric() == False)
        ): return

        seats = getMXSeatSetting(
          seats,
          'Smart Climate!K7',
          'Smart Climate!L7' 
        )        
      elif (day_of_week == 6): # Saturday
        d_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!I8'
        ).execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!J8'
        ).execute().get('values', [])[0][0]

        if (
          (d_temp.isnumeric() == False) 
          or (p_temp.isnumeric() == False)
        ): return

        seats = getMXSeatSetting(
          seats,
          'Smart Climate!K8',
          'Smart Climate!L8' 
        )        
      else:
        return
    elif (wdata['main']['temp'] > hot_temp_threshold):
      # get pre-cool preferences
      if (day_of_week == 0): # Sunday
        d_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!I18'
        ).execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!J18'
        ).execute().get('values', [])[0][0]

        if (
          (d_temp.isnumeric() == False) 
          or (p_temp.isnumeric() == False)
        ): return

        seats = getMXSeatSetting(
          seats,
          'Smart Climate!K18',
          'Smart Climate!L18' 
        )        
      elif (day_of_week == 1): # Monday
        d_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!I12'
        ).execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!J12'
        ).execute().get('values', [])[0][0]

        if (
          (d_temp.isnumeric() == False) 
          or (p_temp.isnumeric() == False)
        ): return

        seats = getMXSeatSetting(
          seats,
          'Smart Climate!K12',
          'Smart Climate!L12' 
        )        
      elif (day_of_week == 2): # Tuesday
        d_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!I13'
        ).execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!J13'
        ).execute().get('values', [])[0][0]

        if (
          (d_temp.isnumeric() == False) 
          or (p_temp.isnumeric() == False)
        ): return

        seats = getMXSeatSetting(
          seats,
          'Smart Climate!K13',
          'Smart Climate!L13' 
        )        
      elif (day_of_week == 3): # Wednesday
        d_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!I14'
        ).execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!J14'
        ).execute().get('values', [])[0][0]

        if (
          (d_temp.isnumeric() == False) 
          or (p_temp.isnumeric() == False)
        ): return

        seats = getMXSeatSetting(
          seats,
          'Smart Climate!K14',
          'Smart Climate!L14' 
        )        
      elif (day_of_week == 4): # Thursday
        d_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!I15'
        ).execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!J15'
        ).execute().get('values', [])[0][0]

        if (
          (d_temp.isnumeric() == False) 
          or (p_temp.isnumeric() == False)
        ): return

        seats = getMXSeatSetting(
          seats,
          'Smart Climate!K15',
          'Smart Climate!L15' 
        )        
      elif (day_of_week == 5): # Friday
        d_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!I16'
        ).execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!J16'
        ).execute().get('values', [])[0][0]

        if (
          (d_temp.isnumeric() == False) 
          or (p_temp.isnumeric() == False)
        ): return

        seats = getMXSeatSetting(
          seats,
          'Smart Climate!K16',
          'Smart Climate!L16' 
        )        
      elif (day_of_week == 6): # Saturday
        d_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!I17'
        ).execute().get('values', [])[0][0]
        p_temp = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Climate!J17'
        ).execute().get('values', [])[0][0]

        if (
          (d_temp.isnumeric() == False) 
          or (p_temp.isnumeric() == False)
        ): return

        seats = getMXSeatSetting(
          seats,
          'Smart Climate!K17',
          'Smart Climate!L17' 
        )        
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
      stop_time = service.spreadsheets().values().get(
        spreadsheetId=EV_SPREADSHEET_ID, 
        range='Smart Climate!I21'
      ).execute().get('values', [])[0][0]

      # specific date/time to create a crontab at the preferred stop time 
      # (this doesn't seem to work outside of AM, might need refactoring)
      estimated_stop_time = datetime(
        datetime.today().year, 
        datetime.today().month, 
        datetime.today().day, 
        stop_time.hour, 
        stop_time.minute
      )

      # create crontab to stop preconditioning
      deleteCronTab('/home/pi/tesla/python/PreconditionMXStop.py')
      createCronTab(
        '/home/pi/tesla/python/PreconditionMXStop.py', 
        estimated_charge_stop_time.hour, 
        estimated_charge_stop_time.minute
      )
    service.close()
  except Exception as e: 
    logError('preconditionMXStart(): ' + str(e))
    wakeVehicle(MX_VIN)
    time.sleep(WAIT_TIME)
    main()

if __name__ == "__main__":
  main()


