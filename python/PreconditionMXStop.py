from TeslaVehicleAPI import getVehicleData, preconditionCarStop
from Utilities import isVehicleAtPrimary, getConfig
from Logger import logError

MX_VIN = getConfig()['vehicle']['mx_vin']

WAIT_TIME = 30 


def preconditionMXStop():
  try:
    data = getVehicleData(MX_VIN)
    if (isVehicleAtPrimary(data) and 
        data['response']['drive_state']['shift_state'] != 'D' and
        data['response']['drive_state']['shift_state'] != 'R' and
        data['response']['drive_state']['shift_state'] != 'N'): # only execute if the car is at primary location and in park
      preconditionCarStop(MX_VIN)
  except Exception as e:
    logError('preconditionMXStop(): ' + str(e))


def main():
  preconditionMXStop()

if __name__ == "__main__":
  main()
