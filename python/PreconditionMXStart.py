from TeslaVehicleAPI import getVehicleData, setCarTemp, setCarSeatHeating, preconditionCarStart
from GoogleAPI import getGoogleSheetService
from Utilities import deleteCronTab, createCronTab, isVehicleAtPrimary, getTodayTime, getCurrentWeather, getConfig
from Logger import logError
from datetime import datetime

config = getConfig()
MX_VIN = config['vehicle']['mx_vin']
EV_SPREADSHEET_ID = config['google']['ev_spreadsheet_id']
PRIMARY_LAT = float(config['vehicle']['primary_lat'])
PRIMARY_LNG = float(config['vehicle']['primary_lng'])

WAIT_TIME = 30 


def preconditionMXStart():
  try:
    # get configuration info
    service = getGoogleSheetService()
    climate_config = service.spreadsheets().values().get(
      spreadsheetId=EV_SPREADSHEET_ID, 
      range='Smart Climate!A3:P22'
    ).execute().get('values', [])
    service.close()

    # check if eco mode is on first so we don't have to even call the Tesla API if we don't have to
    if (climate_config[19][10] == 'on'): return
    
    # get local weather
    wdata = getCurrentWeather(PRIMARY_LAT, PRIMARY_LNG)
#    print('temp: ' + str(wdata['current']['temp']))    

#    print('cold temp threshold: ' + climate_config[17][10])
#    print('hot temp threshold: ' + climate_config[18][10])

    # get today's day of week to compare against Google Sheet temp preferences 
    # for that day
    day_of_week = datetime.today().strftime('%A')
    dow_index = [index for index, element in enumerate(climate_config) if day_of_week in element]
    seats = []
    
    # compare temp readings and threshold to determine heating or cooling temps 
    # to use
    if (wdata['current']['temp'] < float(climate_config[17][10])):
      # get pre-heat preferences
      try:
        d_temp = float(climate_config[dow_index[0]][10])
        p_temp = float(climate_config[dow_index[0]][11])
      except ValueError:
        return

      seats.append(climate_config[dow_index[0]][12])
      seats.append(climate_config[dow_index[0]][13])

      stop_time = getTodayTime(climate_config[dow_index[0]][15])
    elif (wdata['current']['temp'] > float(climate_config[18][10])):
      # get pre-cool preferences
      try:
        d_temp = float(climate_config[dow_index[1]][10])
        p_temp = float(climate_config[dow_index[1]][11])
      except ValueError:
        return

      seats.append(climate_config[dow_index[1]][12])
      seats.append(climate_config[dow_index[1]][13])

      stop_time = getTodayTime(climate_config[dow_index[1]][15])
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
      
      # create crontab to stop preconditioning at preferred time later in the day
      deleteCronTab('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/PreconditionMXStop.py >> /home/pi/tesla/python/cron.log 2>&1')
      createCronTab(
        '/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/PreconditionMXStop.py >> /home/pi/tesla/python/cron.log 2>&1', 
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


