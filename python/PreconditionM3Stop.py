import time

from TeslaVehicleAPI import getVehicleData
from Utilities import isVehicleAtHome
from Logger import logError

M3_VIN = ''
WAIT_TIME = 30

def main():
  try:
    data = getVehicleData(M3_VIN)
    if (isVehicleAtHome(data)): # no need to execute if unsure where the car is or if it's in motion
      preconditionCarStop(M3_VIN)
  except Exception as e:
    logError('preconditionM3Stop(): ' + e)
    wakeVehicle(M3_VIN)
    time.sleep(WAIT_TIME)
    preconditionM3Stop()

if __name__ == "__main__":
  main()
