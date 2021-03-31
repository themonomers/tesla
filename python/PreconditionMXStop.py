import time

from TeslaVehicleAPI import getVehicleData
from Utilities import isVehicleAtHome
from Logger import logError

MX_VIN = ''
WAIT_TIME = 30

def main():
  try:
    data = getVehicleData(MX_VIN)
    if (isVehicleAtHome(data)): # no need to execute if unsure where the car is or if it's in motion
      preconditionCarStop(MX_VIN)
  except Exception as e:
    logError('preconditionMXStop(): ' + e)
    wakeVehicle(MX_VIN)
    time.sleep(WAIT_TIME)
    main()

if __name__ == "__main__":
  main()
