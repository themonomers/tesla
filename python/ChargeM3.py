import time
import configparser
import os

from TeslaVehicleAPI import chargeVehicle, wakeVehicle
from Crypto import decrypt
from Logger import logError
from io import StringIO

buffer = StringIO(
  decrypt(
    os.path.join(
      os.path.dirname(os.path.abspath(__file__)),
      'config.rsa'
    )
  ).decode('utf-8')
)
config = configparser.ConfigParser()
config.sections()
config.readfp(buffer)
M3_VIN = config['vehicle']['m3_vin']
buffer.close()

WAIT_TIME = 30


##
# Function to be set on a crontab and will repeat if the car isn't awake.  
# If the car isn't awake, the API call will throw an exception and will try 
# to repeatedly wake the vehicle and rerun this function.
#
# author: mjhwa@yahoo.com
##
def chargeM3():
  try:
    # add check to see if car is already charging or do nothing else since 
    # sending a charge command while it's charging doesn't do anything.
    chargeVehicle(M3_VIN)
  except Exception as e:
    logError('chargeM3(): ' + str(e))
    wakeVehicle(M3_VIN)
    time.sleep(WAIT_TIME)
    chargeM3()


def main():
  chargeM3()

if __name__ == "__main__":
  main()
