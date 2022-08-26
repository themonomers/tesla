import time

from TeslaVehicleAPI import wakeVehicle, getVehicleData, preconditionCarStop
from Utilities import isVehicleAtPrimary, getConfig
from Logger import logError

MX_VIN = getConfig()['vehicle']['mx_vin']

WAIT_TIME = 30 


def preconditionMXStop():
  try:
    data = getVehicleData(MX_VIN)
    if (isVehicleAtPrimary(data) and 
         (data['response']['drive_state']['shift_state'] == 'P' or
          data['response']['drive_state']['shift_state'] == 'None')
       ): # only execute if the car is at primary location and in park
      preconditionCarStop(MX_VIN)
  except Exception as e:
    logError('preconditionMXStop(): ' + str(e))
    wakeVehicle(MX_VIN)
    time.sleep(WAIT_TIME)
    preconditionMXStop()


def main():
  preconditionMXStop()

if __name__ == "__main__":
  main()
