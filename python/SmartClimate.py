from Utilities import isVehicleAtPrimary, getTomorrowTime, deleteCronTab, createCronTab
from Logger import logError


##
# Creates a trigger to precondition the cabin for the following morning, 
# based on if the car is at the primary location and if "Eco Mode" is off 
# similar to how Nest thermostats work for vacation scenarios.  With the 
# new endpoints released, you can achieve the same functionality by setting 
# scheduled departure for preconditioning.  I decided to keep this code 
# running as I don't drive long distances so the added feature of 
# preconditioning the battery, in addition to the cabin, is a waste of 
# energy (entropy) for me.
#
# author: mjhwa@yahoo.com
## 
def setM3Precondition(data, climate_config):
  try: 
    # check if eco mode is off first so we don't have to even call the 
    # Tesla API if we don't have to
    if (climate_config[4][0] == 'off'):
      # check if the car is with 0.25 miles of the primary location
      if (isVehicleAtPrimary(data)):
        # specific date/time to create a crontab for tomorrow morning at 
        # the preferred start time
        start_time = getTomorrowTime(climate_config[0][0])
        
        # create precondition start crontab
        deleteCronTab('python /home/pi/tesla/python/PreconditionM3Start.py')
        createCronTab('python /home/pi/tesla/python/PreconditionM3Start.py', 
                      start_time.month, 
                      start_time.day, 
                      start_time.hour, 
                      start_time.minute)
  except Exception as e:
    logError('setM3Precondition(): ' + str(e))


def setMXPrecondition(data, climate_config):
  try: 
    # check if eco mode is off first so we don't have to even call the 
    # Tesla API if we don't have to
    if (climate_config[4][7] == 'off'):
      # check if the car is with 0.25 miles of the primary location
      if (isVehicleAtPrimary(data)):
        # specific date/time to create a crontab for tomorrow morning at 
        # the preferred start time
        start_time = getTomorrowTime(climate_config[0][7])

        # create precondition start crontab
        deleteCronTab('python /home/pi/tesla/python/PreconditionMXStart.py')
        createCronTab('python /home/pi/tesla/python/PreconditionMXStart.py', 
                      start_time.month, 
                      start_time.day, 
                      start_time.hour, 
                      start_time.minute)
  except Exception as e:
    logError('setMXPrecondition(): ' + str(e))