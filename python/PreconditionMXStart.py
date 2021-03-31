import time

from TeslaVehicleAPI import *
from GoogleAPI import *
from Utilities import *
from Logger import *
from datetime import timedelta, datetime

MX_VIN = ''
WAIT_TIME = 30
TEST_EV_SPREADSHEET_ID = ''

def main():
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
    main();

if __name__ == "__main__":
  main()
