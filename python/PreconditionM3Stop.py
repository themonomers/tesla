import time
import configparser

from TeslaVehicleAPI import wakeVehicle, getVehicleData, preconditionCarStop
from Utilities import isVehicleAtHome
from Crypto import decrypt
from Logger import logError
from io import StringIO

buffer = StringIO(decrypt('config.rsa').decode('utf-8'))
config = configparser.ConfigParser()
config.sections()
config.readfp(buffer)
M3_VIN = config['vehicle']['m3_vin']
buffer.close()

WAIT_TIME = 30 


def main():
  try:
    data = getVehicleData(M3_VIN)
    if (isVehicleAtHome(data)): # no need to execute if unsure where the car is or if it's in motion
      preconditionCarStop(M3_VIN)
  except Exception as e:
    logError('preconditionM3Stop(): ' + str(e))
    wakeVehicle(M3_VIN)
    time.sleep(WAIT_TIME)
    main()

if __name__ == "__main__":
  main()
