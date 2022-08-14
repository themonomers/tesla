import time

from TeslaVehicleAPI import getVehicleData, wakeVehicle, setCarTemp, setCarSeatHeating, preconditionCarStart
from GoogleAPI import getGoogleSheetService
from Utilities import deleteCronTab, createCronTab, isVehicleAtPrimary, getTomorrowTime, getCurrentWeather, getConfig
from Logger import logError
from datetime import datetime

config = getConfig()
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
def preconditionM3Start():
  try:
    # get configuration info
    service = getGoogleSheetService()
    grid = service.spreadsheets().values().get(
      spreadsheetId=EV_SPREADSHEET_ID, 
      range='Smart Climate!B3:H24'
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
        seats.append(grid[0][4])
        seats.append(-1) # placeholder for index 3 as it's not assigned in the API
        seats.append(grid[0][5])
        seats.append(grid[0][6])
      elif (day_of_week == 1): # Tuesday
        try:
          d_temp = float(grid[1][0])
          p_temp = float(grid[1][1])
        except ValueError:
         return

        seats.append(grid[1][2])
        seats.append(grid[1][3])
        seats.append(grid[1][4])
        seats.append(-1) # placeholder for index 3 as it's not assigned in the API
        seats.append(grid[1][5])
        seats.append(grid[1][6])
      elif (day_of_week == 2): # Wednesday
        try:
          d_temp = float(grid[2][0])
          p_temp = float(grid[2][1])
        except ValueError:
         return

        seats.append(grid[2][2])
        seats.append(grid[2][3])
        seats.append(grid[2][4])
        seats.append(-1) # placeholder for index 3 as it's not assigned in the API
        seats.append(grid[2][5])
        seats.append(grid[2][6])
      elif (day_of_week == 3): # Thursday
        try:
          d_temp = float(grid[3][0])
          p_temp = float(grid[3][1])
        except ValueError:
         return

        seats.append(grid[3][2])
        seats.append(grid[3][3])
        seats.append(grid[3][4])
        seats.append(-1) # placeholder for index 3 as it's not assigned in the API
        seats.append(grid[3][5])
        seats.append(grid[3][6])
      elif (day_of_week == 4): # Friday
        try:
          d_temp = float(grid[4][0])
          p_temp = float(grid[4][1])
        except ValueError:
         return

        seats.append(grid[4][2])
        seats.append(grid[4][3])
        seats.append(grid[4][4])
        seats.append(-1) # placeholder for index 3 as it's not assigned in the API
        seats.append(grid[4][5])
        seats.append(grid[4][6])
      elif (day_of_week == 5): # Saturday
        try:
          d_temp = float(grid[5][0])
          p_temp = float(grid[5][1])
        except ValueError:
         return

        seats.append(grid[5][2])
        seats.append(grid[5][3])
        seats.append(grid[5][4])
        seats.append(-1) # placeholder for index 3 as it's not assigned in the API
        seats.append(grid[5][5])
        seats.append(grid[5][6])
      elif (day_of_week == 6):  # Sunday
        try:
          d_temp = float(grid[6][0])
          p_temp = float(grid[6][1])
        except ValueError:
         return

        seats.append(grid[6][2])
        seats.append(grid[6][3])
        seats.append(grid[6][4])
        seats.append(-1) # placeholder for index 3 as it's not assigned in the API
        seats.append(grid[6][5])
        seats.append(grid[6][6])
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
        seats.append(grid[9][4])
        seats.append(-1) # placeholder for index 3 as it's not assigned in the API
        seats.append(grid[9][5])
        seats.append(grid[9][6])   
      elif (day_of_week == 1): # Tuesday
        try:
          d_temp = float(grid[10][0])
          p_temp = float(grid[10][1])
        except ValueError:
         return

        seats.append(grid[10][2])
        seats.append(grid[10][3])
        seats.append(grid[10][4])
        seats.append(-1) # placeholder for index 3 as it's not assigned in the API
        seats.append(grid[10][5])
        seats.append(grid[10][6])          
      elif (day_of_week == 2): # Wednesday
        try:
          d_temp = float(grid[11][0])
          p_temp = float(grid[11][1])
        except ValueError:
         return

        seats.append(grid[11][2])
        seats.append(grid[11][3])
        seats.append(grid[11][4])
        seats.append(-1) # placeholder for index 3 as it's not assigned in the API
        seats.append(grid[11][5])
        seats.append(grid[11][6])           
      elif (day_of_week == 3): # Thursday
        try:
          d_temp = float(grid[12][0])
          p_temp = float(grid[12][1])
        except ValueError:
         return

        seats.append(grid[12][2])
        seats.append(grid[12][3])
        seats.append(grid[12][4])
        seats.append(-1) # placeholder for index 3 as it's not assigned in the API
        seats.append(grid[12][5])
        seats.append(grid[12][6])      
      elif (day_of_week == 4): # Friday
        try:
          d_temp = float(grid[13][0])
          p_temp = float(grid[13][1])
        except ValueError:
         return

        seats.append(grid[13][2])
        seats.append(grid[13][3])
        seats.append(grid[13][4])
        seats.append(-1) # placeholder for index 3 as it's not assigned in the API
        seats.append(grid[13][5])
        seats.append(grid[13][6]) 
      elif (day_of_week == 5): # Saturday
        try:
          d_temp = float(grid[14][0])
          p_temp = float(grid[14][1])
        except ValueError:
         return

        seats.append(grid[14][2])
        seats.append(grid[14][3])
        seats.append(grid[14][4])
        seats.append(-1) # placeholder for index 3 as it's not assigned in the API
        seats.append(grid[14][5])
        seats.append(grid[14][6]) 
      elif (day_of_week == 6): # Sunday
        try:
          d_temp = float(grid[15][0])
          p_temp = float(grid[15][1])
        except ValueError:
         return

        seats.append(grid[15][2])
        seats.append(grid[15][3])
        seats.append(grid[15][4])
        seats.append(-1) # placeholder for index 3 as it's not assigned in the API
        seats.append(grid[15][5])
        seats.append(grid[15][6])     
      else:
        return
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
        setCarSeatHeating(M3_VIN, index, item)

      # specific date/time to create a crontab for tomorrow morning at 
      # the preferred stop time
      stop_time = getTomorrowTime(grid[18][0])
      
      # create crontab to stop preconditioning
      deleteCronTab('python /home/pi/tesla/python/PreconditionM3Stop.py')
      createCronTab(
        'python /home/pi/tesla/python/PreconditionM3Stop.py', 
        stop_time.month, 
        stop_time.day, 
        stop_time.hour, 
        stop_time.minute
      )
  except Exception as e:
    logError('preconditionM3Start(): ' + str(e))
    wakeVehicle(M3_VIN)
    time.sleep(WAIT_TIME)
    preconditionM3Start()


def main():
  preconditionM3Start()

if __name__ == "__main__":
  main()

