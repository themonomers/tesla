import time

from TeslaVehicleAPI import chargeVehicle, wakeVehicle
from Logger import *

MX_VIN = ''
WAIT_TIME = 30

##
# Function to be set on a crontab and will repeat if the car isn't awake.
# If the car isn't awake, the API call will throw an exception and will try
# to repeatedly wake the vehicle and rerun this function.
#
# author: mjhwa@yahoo.com
##
def main():
  try:
    # add check to see if car is already charging or do nothing else since
    # sending a charge command while it's charging doesn't do anything.
    chargeVehicle(MX_VIN);
  except Exception as e:
    print('chargeMX(): ' + e)
    logError('chargeMX(): ' + e)
    wakeVehicle(MX_VIN)
    time.sleep(WAIT_TIME)
    main()

if __name__ == "__main__":
  main()
