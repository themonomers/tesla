import time

from TeslaVehicleAPI import chargeVehicle, wakeVehicle
from Logger import *

M3_VIN = ''
WAIT_TIME = 30

##
# Function to be set on a crontab to run after the main crontab, in case the
# main crontab times out and fails to run.  This redundancy is necessary
# because charging is a critical function and we don't want to wake up to a
# car that's not ready to go.
#
# author: mjhwa@yahoo.com
##
def main():
  try:
    # add check to see if car is already charging or do nothing else since
    # sending a charge command while it's charging doesn't do anything.
    chargeVehicle(M3_VIN);
  except Exception as e:
    print('chargeM3Backup(): ' + e)
    logError('chargeM3Backup(): ' + e)
    wakeVehicle(M3_VIN)
    time.sleep(WAIT_TIME)
    main()

if __name__ == "__main__":
  main()