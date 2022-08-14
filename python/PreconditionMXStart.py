import time

from TeslaVehicleAPI import getVehicleData, wakeVehicle, setCarTemp, setCarSeatHeating, preconditionCarStart
from GoogleAPI import getGoogleSheetService
from Utilities import deleteCronTab, createCronTab, isVehicleAtPrimary, getTomorrowTime, getCurrentWeather, getConfig
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
    grid = service.spreadsheets().values().get(
      spreadsheetId=EV_SPREADSHEET_ID, 
      range='Smart Climate!I3:L24'
    ).execute().get('values', [])
    service.close()

    # check if eco mode is on first so we don't have to even call the Tesla API if we don't have to
    if (grid[21][0] == 'on'): return
    
    # get local weather
    wdata = getCurrentWeather(ZIPCODE)
#    print('temp: ' + str(wdata['main']['temp']))    

#    print('cold temp threshold: ' + grid[19][0])
#    print('hot temp threshold: ' + grid[20][0])

    # get today's day of week to compare against Google Sheet temp preferences 
    # for that day
    day_of_week = datetime.today().weekday()
    seats = []
    
    # compare temp readings and threshold to determine heating or cooling temps 
    # to use
    if (wdata['main']['temp'] < grid[19][0]):
      # get pre-heat preferences
      if (day_of_week == 0): # Monday
        try:
          d_temp = float(grid[0][0])
          p_temp = float(grid[0][1])
        except ValueError:
         return

        seats.append(grid[0][2])
        seats.append(grid[0][3])       
      elif (day_of_week == 1): # Tuesday
        try:
          d_temp = float(grid[1][0])
          p_temp = float(grid[1][1])
        except ValueError:
         return

        seats.append(grid[1][2])
        seats.append(grid[1][3])        
      elif (day_of_week == 2): # Wednesday
        try:
          d_temp = float(grid[2][0])
          p_temp = float(grid[2][1])
        except ValueError:
         return

        seats.append(grid[2][2])
        seats.append(grid[2][3])      
      elif (day_of_week == 3): # Thursday
        try:
          d_temp = float(grid[3][0])
          p_temp = float(grid[3][1])
        except ValueError:
         return

        seats.append(grid[3][2])
        seats.append(grid[3][3])        
      elif (day_of_week == 4): # Friday
        try:
          d_temp = float(grid[4][0])
          p_temp = float(grid[4][1])
        except ValueError:
         return

        seats.append(grid[4][2])
        seats.append(grid[4][3])         
      elif (day_of_week == 5): # Saturday
        try:
          d_temp = float(grid[5][0])
          p_temp = float(grid[5][1])
        except ValueError:
         return

        seats.append(grid[5][2])
        seats.append(grid[5][3])         
      elif (day_of_week == 6): # Sunday
        try:
          d_temp = float(grid[6][0])
          p_temp = float(grid[6][1])
        except ValueError:
         return
        
        seats.append(grid[6][2])
        seats.append(grid[6][3])  
      else:
        return
    elif (wdata['main']['temp'] > grid[20][0]):
      # get pre-cool preferences
      if (day_of_week == 0): # Monday
        try:
          d_temp = float(grid[9][0])
          p_temp = float(grid[9][1])
        except ValueError:
         return

        seats.append(grid[9][2])
        seats.append(grid[9][3])    
      elif (day_of_week == 1): # Tuesday
        try:
          d_temp = float(grid[10][0])
          p_temp = float(grid[10][1])
        except ValueError:
         return

        seats.append(grid[10][2])
        seats.append(grid[10][3])     
      elif (day_of_week == 2): # Wednesday
        try:
          d_temp = float(grid[11][0])
          p_temp = float(grid[11][1])
        except ValueError:
         return

        seats.append(grid[11][2])
        seats.append(grid[11][3])     
      elif (day_of_week == 3): # Thursday
        try:
          d_temp = float(grid[12][0])
          p_temp = float(grid[12][1])
        except ValueError:
         return

        seats.append(grid[12][2])
        seats.append(grid[12][3])     
      elif (day_of_week == 4): # Friday
        try:
          d_temp = float(grid[13][0])
          p_temp = float(grid[13][1])
        except ValueError:
         return

        seats.append(grid[13][2])
        seats.append(grid[13][3])     
      elif (day_of_week == 5): # Saturday
        try:
          d_temp = float(grid[14][0])
          p_temp = float(grid[14][1])
        except ValueError:
         return

        seats.append(grid[14][2])
        seats.append(grid[14][3])     
      elif (day_of_week == 6): # Sunday
        try:
          d_temp = float(grid[15][0])
          p_temp = float(grid[15][1])
        except ValueError:
         return

        seats.append(grid[15][2])
        seats.append(grid[15][3])
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
        setCarSeatHeating(MX_VIN, index, item)
      
      # specific date/time to create a crontab for tomorrow morning at 
      # the preferred stop time
      stop_time = getTomorrowTime(grid[18][0])

      # create crontab to stop preconditioning
      deleteCronTab('python /home/pi/tesla/python/PreconditionMXStop.py')
      createCronTab(
        'python /home/pi/tesla/python/PreconditionMXStop.py', 
        stop_time.month, 
        stop_time.day, 
        stop_time.hour, 
        stop_time.minute
      )
  except Exception as e: 
    logError('preconditionMXStart(): ' + str(e))
    wakeVehicle(MX_VIN)
    time.sleep(WAIT_TIME)
    preconditionMXStart()


def main():
  preconditionMXStart()

if __name__ == "__main__":
  main()


