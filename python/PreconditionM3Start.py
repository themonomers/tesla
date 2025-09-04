from TeslaVehicleAPI import getVehicleData, setCarTemp, setCarSeatHeating, preconditionCarStart
from GoogleAPI import getGoogleSheetService
from Utilities import deleteCronTab, createCronTab, isVehicleAtPrimary, getTodayTime, getCurrentWeather, getConfig
from Logger import logError
from datetime import datetime

config = getConfig()
M3_VIN = config['vehicle']['m3_vin']
EV_SPREADSHEET_ID = config['google']['ev_spreadsheet_id'] 
PRIMARY_LAT = float(config['vehicle']['primary_lat'])
PRIMARY_LNG = float(config['vehicle']['primary_lng'])

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
def preconditionM3Start():
  try:
    # get configuration info
    service = getGoogleSheetService()
    climate_config = service.spreadsheets().values().get(
      spreadsheetId=EV_SPREADSHEET_ID, 
      range='Smart Climate!A3:P22'
    ).execute().get('values', [])
    service.close()

    # check if eco mode is on first so we don't have to even call the Tesla API if we don't have to
    if (climate_config[19][1] == 'on'): return
    
    # get local weather
    wdata = getCurrentWeather(PRIMARY_LAT, PRIMARY_LNG)
#    print('temp: ' + str(wdata['current']['temp']))
    
#    print('cold temp threshold: ' + climate_config[17][1])
#    print('hot temp threshold: ' + climate_config[18][1])

    # get today's day of week to compare against Google Sheet temp preferences 
    # for that day
    day_of_week = datetime.today().strftime('%A')
    dow_index = [index for index, element in enumerate(climate_config) if day_of_week in element]
    seats = []
    
    # compare temp readings and threshold to determine heating or cooling temps 
    # to use
    if (wdata['current']['temp'] < float(climate_config[17][1])):
      # get pre-heat preferences  
      try:
        d_temp = float(climate_config[dow_index[0]][1])
        p_temp = float(climate_config[dow_index[0]][2])
      except ValueError:
        return

      seats.append(climate_config[dow_index[0]][3])
      seats.append(climate_config[dow_index[0]][4])
      seats.append(climate_config[dow_index[0]][5])
      seats.append(-1) # placeholder for index 3 as it's not assigned in the API
      seats.append(climate_config[dow_index[0]][6])
      seats.append(climate_config[dow_index[0]][7])

      stop_time = getTodayTime(climate_config[dow_index[0]][9])
    elif (wdata['current']['temp'] > float(climate_config[18][1])):
      # get pre-cool preferences
      try:
        d_temp = float(climate_config[dow_index[1]][1])
        p_temp = float(climate_config[dow_index[1]][2])
      except ValueError:
        return

      seats.append(climate_config[dow_index[1]][3])
      seats.append(climate_config[dow_index[1]][4])
      seats.append(climate_config[dow_index[1]][5])
      seats.append(-1) # placeholder for index 3 as it's not assigned in the API
      seats.append(climate_config[dow_index[1]][6])
      seats.append(climate_config[dow_index[1]][7])

      stop_time = getTodayTime(climate_config[dow_index[1]][9])
    else:
      return # outside temp is within cold and hot thresholds so no preconditioning required; inside and outside car temp readings seem to be inaccurate until the HVAC runs

    #print('d_temp: ' + str(d_temp))
    #print('p_temp: ' + str(p_temp))
    #print('seats: ' + str(seats))
    # no need to execute if unsure where the car is or if it's in motion
    data = getVehicleData(M3_VIN)
    if (isVehicleAtPrimary(data)):
      # send command to start auto conditioning
      preconditionCarStart(M3_VIN)

      # set driver and passenger temps
      setCarTemp(M3_VIN, d_temp, p_temp)
      
      # set seat heater settings
      for index, item in enumerate(seats):
        if (index == 3):
          continue # skip index 3 as it's not assigned in the API
        setCarSeatHeating(M3_VIN, int(index), int(item))

      # create crontab to stop preconditioning at preferred time later in the day
      deleteCronTab('/usr/bin/timeout -k 360 300 python /home/pi/tesla/python/PreconditionM3Stop.py >> /home/pi/tesla/python/cron.log 2>&1')
      createCronTab(
        '/usr/bin/timeout -k 360 300 python /home/pi/tesla/python/PreconditionM3Stop.py >> /home/pi/tesla/python/cron.log 2>&1', 
        stop_time.month, 
        stop_time.day, 
        stop_time.hour, 
        stop_time.minute
      )
  except Exception as e:
    logError('preconditionM3Start(): ' + str(e))


def main():
  preconditionM3Start()

if __name__ == "__main__":
  main()

