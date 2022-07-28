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
M3_VIN = config['vehicle']['m3_vin']
buffer.close()

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
    if (isVehicleAtHome(data)): # no need to execute if unsure where the car is or if it's in motion
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
