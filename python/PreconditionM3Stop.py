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
    if (isVehicleAtPrimary(data)): # no need to execute if unsure where the car is or if it's in motion
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
