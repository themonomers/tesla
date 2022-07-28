import time
import configparser
import os

from TeslaVehicleAPI import wakeVehicle, getVehicleData, preconditionCarStop
from Utilities import isVehicleAtHome
from Crypto import simpleDecrypt
from Logger import logError
from io import StringIO

buffer = StringIO(
  simpleDecrypt(
    os.path.join(
      os.path.dirname(os.path.abspath(__file__)),
      'config.xor'
    ),
    os.path.join(
      os.path.dirname(os.path.abspath(__file__)),
      'config_key'
    )
  )
)
config = configparser.ConfigParser()
config.sections()
config.read_file(buffer)
MX_VIN = config['vehicle']['mx_vin']
buffer.close()

WAIT_TIME = 30 


def preconditionMXStop():
  try:
    data = getVehicleData(MX_VIN)
    if (isVehicleAtHome(data)): # no need to execute if unsure where the car is or if it's in motion
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
