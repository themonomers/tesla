from TeslaVehicleAPI import getVehicleData, setCarTemp, setCarSeatHeating, preconditionCarStart
from GoogleAPI import getGoogleSheetService
from Utilities import deleteCronTab, createCronTab, isVehicleAtPrimary, getTodayTime, getCurrentWeather, getConfig
from Logger import logError
from datetime import datetime

config = getConfig()
MX_VIN = config['vehicle']['mx_vin']
EV_SPREADSHEET_ID = config['google']['ev_spreadsheet_id']
ZIPCODE = config['weather']['zipcode']

WAIT_TIME = 30 


def preconditionMXStart():
  try:
    # get configuration info
    service = getGoogleSheetService()
    climate_config = service.spreadsheets().values().get(
      spreadsheetId=EV_SPREADSHEET_ID, 
      range='Smart Climate!I3:L24'
    ).execute().get('values', [])
    service.close()

    # check if eco mode is on first so we don't have to even call the Tesla API if we don't have to
    if (climate_config[21][0] == 'on'): return
    
    # get local weather
    wdata = getCurrentWeather(ZIPCODE)
#    print('temp: ' + str(wdata['main']['temp']))    

#    print('cold temp threshold: ' + climate_config[19][0])
#    print('hot temp threshold: ' + climate_config[20][0])

    # get today's day of week to compare against Google Sheet temp preferences 
    # for that day
    day_of_week = datetime.today().weekday()
    seats = []
    
    # compare temp readings and threshold to determine heating or cooling temps 
    # to use
    if (wdata['main']['temp'] < float(climate_config[19][0])):
      # get pre-heat preferences
      if (day_of_week == 0): # Monday
        try:
          d_temp = float(climate_config[0][0])
          p_temp = float(climate_config[0][1])
        except ValueError:
         return

        seats.append(climate_config[0][2])
        seats.append(climate_config[0][3])       
      elif (day_of_week == 1): # Tuesday
        try:
          d_temp = float(climate_config[1][0])
          p_temp = float(climate_config[1][1])
        except ValueError:
         return

        seats.append(climate_config[1][2])
        seats.append(climate_config[1][3])        
      elif (day_of_week == 2): # Wednesday
        try:
          d_temp = float(climate_config[2][0])
          p_temp = float(climate_config[2][1])
        except ValueError:
         return

        seats.append(climate_config[2][2])
        seats.append(climate_config[2][3])      
      elif (day_of_week == 3): # Thursday
        try:
          d_temp = float(climate_config[3][0])
          p_temp = float(climate_config[3][1])
        except ValueError:
         return

        seats.append(climate_config[3][2])
        seats.append(climate_config[3][3])        
      elif (day_of_week == 4): # Friday
        try:
          d_temp = float(climate_config[4][0])
          p_temp = float(climate_config[4][1])
        except ValueError:
         return

        seats.append(climate_config[4][2])
        seats.append(climate_config[4][3])         
      elif (day_of_week == 5): # Saturday
        try:
          d_temp = float(climate_config[5][0])
          p_temp = float(climate_config[5][1])
        except ValueError:
         return

        seats.append(climate_config[5][2])
        seats.append(climate_config[5][3])         
      elif (day_of_week == 6): # Sunday
        try:
          d_temp = float(climate_config[6][0])
          p_temp = float(climate_config[6][1])
        except ValueError:
         return
        
        seats.append(climate_config[6][2])
        seats.append(climate_config[6][3])  
      else:
        return
    elif (wdata['main']['temp'] > float(climate_config[20][0])):
      # get pre-cool preferences
      if (day_of_week == 0): # Monday
        try:
          d_temp = float(climate_config[9][0])
          p_temp = float(climate_config[9][1])
        except ValueError:
         return

        seats.append(climate_config[9][2])
        seats.append(climate_config[9][3])    
      elif (day_of_week == 1): # Tuesday
        try:
          d_temp = float(climate_config[10][0])
          p_temp = float(climate_config[10][1])
        except ValueError:
         return

        seats.append(climate_config[10][2])
        seats.append(climate_config[10][3])     
      elif (day_of_week == 2): # Wednesday
        try:
          d_temp = float(climate_config[11][0])
          p_temp = float(climate_config[11][1])
        except ValueError:
         return

        seats.append(climate_config[11][2])
        seats.append(climate_config[11][3])     
      elif (day_of_week == 3): # Thursday
        try:
          d_temp = float(climate_config[12][0])
          p_temp = float(climate_config[12][1])
        except ValueError:
         return

        seats.append(climate_config[12][2])
        seats.append(climate_config[12][3])     
      elif (day_of_week == 4): # Friday
        try:
          d_temp = float(climate_config[13][0])
          p_temp = float(climate_config[13][1])
        except ValueError:
         return

        seats.append(climate_config[13][2])
        seats.append(climate_config[13][3])     
      elif (day_of_week == 5): # Saturday
        try:
          d_temp = float(climate_config[14][0])
          p_temp = float(climate_config[14][1])
        except ValueError:
         return

        seats.append(climate_config[14][2])
        seats.append(climate_config[14][3])     
      elif (day_of_week == 6): # Sunday
        try:
          d_temp = float(climate_config[15][0])
          p_temp = float(climate_config[15][1])
        except ValueError:
         return

        seats.append(climate_config[15][2])
        seats.append(climate_config[15][3])
      else:
        return
    else:
      return # outside temp is within cold and hot thresholds so no preconditioning required; inside and outside car temp readings seem to be inaccurate until the HVAC runs

    #print('d_temp: ' + str(d_temp))
    #print('p_temp: ' + str(p_temp))
    #print('seats: ' + str(seats))
    # no need to execute if unsure where the car is or if it's in motion
    data = getVehicleData(MX_VIN)
    if (isVehicleAtPrimary(data)):
      # send command to start auto conditioning
      preconditionCarStart(MX_VIN)

      # set driver and passenger temps
      setCarTemp(MX_VIN, d_temp, p_temp)

      # set seat heater settings
      for index, item in enumerate(seats):
        setCarSeatHeating(MX_VIN, int(index), int(item))
      
      # specific date/time to create a crontab for later this morning at 
      # the preferred stop time
      stop_time = getTodayTime(climate_config[18][0])

      # create crontab to stop preconditioning
      deleteCronTab('/usr/bin/timeout -k 360 300 python /home/pi/tesla/python/PreconditionMXStop.py >> /home/pi/tesla/python/cron.log 2>&1')
      createCronTab(
        '/usr/bin/timeout -k 360 300 python /home/pi/tesla/python/PreconditionMXStop.py >> /home/pi/tesla/python/cron.log 2>&1', 
        stop_time.month, 
        stop_time.day, 
        stop_time.hour, 
        stop_time.minute
      )
  except Exception as e: 
    logError('preconditionMXStart(): ' + str(e))


def main():
  preconditionMXStart()

if __name__ == "__main__":
  main()


