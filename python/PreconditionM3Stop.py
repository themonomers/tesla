import time

from TeslaVehicleAPI import wakeVehicle, getVehicleData, preconditionCarStop
from Utilities import isVehicleAtPrimary, getConfig
from Logger import logError

M3_VIN = getConfig()['vehicle']['m3_vin']

WAIT_TIME = 30 


##
# Sends command to stop vehicle preconditioning based on a previously scheduled
# crontab configured in a Google Sheet.
#
# author: mjhwa@yahoo.com
##
def preconditionM3Stop():
  try:
    data = getVehicleData(M3_VIN)
    if (isVehicleAtPrimary(data) and 
         (data['response']['drive_state']['shift_state'] == 'P' or
          data['response']['drive_state']['shift_state'] == 'None')
       ): # only execute if the car is at primary location and in park
      preconditionCarStop(M3_VIN)
  except Exception as e:
    logError('preconditionM3Stop(): ' + str(e))
    wakeVehicle(M3_VIN)
    time.sleep(WAIT_TIME)
    preconditionM3Stop()


def main():
  preconditionM3Stop()

if __name__ == "__main__":
  main()
