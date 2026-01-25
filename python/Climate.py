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
def setM3Precondition(data, eco_mode, start_time):
  try: 
    # check if eco mode is off first so we don't have to even call the 
    # Tesla API if we don't have to
    if (eco_mode == 'off'):
      # check if the car is with 0.25 miles of the primary location
      if (isVehicleAtPrimary(data)):
        # create precondition start crontab at preferred time tomorrow
        deleteCronTab('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/PreconditionM3Start.py >> /home/pi/tesla/python/cron.log 2>&1')
        createCronTab('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/PreconditionM3Start.py >> /home/pi/tesla/python/cron.log 2>&1', 
                      start_time.month, 
                      start_time.day, 
                      start_time.hour, 
                      start_time.minute)
        
        return start_time
    return None
  except Exception as e:
    logError('setM3Precondition(): ' + str(e))


def setMXPrecondition(data, eco_mode, start_time):
  try: 
    # check if eco mode is off first so we don't have to even call the 
    # Tesla API if we don't have to
    if (eco_mode == 'off'):
      # check if the car is with 0.25 miles of the primary location
      if (isVehicleAtPrimary(data)):
        # create precondition start crontab at preferred time tomorrow
        deleteCronTab('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/PreconditionMXStart.py >> /home/pi/tesla/python/cron.log 2>&1')
        createCronTab('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/PreconditionMXStart.py >> /home/pi/tesla/python/cron.log 2>&1', 
                      start_time.month, 
                      start_time.day, 
                      start_time.hour, 
                      start_time.minute)
        
        return start_time
    return None
  except Exception as e:
    logError('setMXPrecondition(): ' + str(e))