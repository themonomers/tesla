import time
import configparser

from TeslaVehicleAPI import chargeVehicle, wakeVehicle
from Crypto import decrypt
from Logger import logError
from io import StringIO

buffer = StringIO(decrypt('/home/pi/tesla/python/config.rsa').decode('utf-8'))
config = configparser.ConfigParser()
config.sections()
config.readfp(buffer)
MX_VIN = config['vehicle']['mx_vin']
buffer.close()

WAIT_TIME = 30


##
# Function to be set on a crontab to run after the main crontab, in case the 
# main crontab times out and fails to run.  This redundancy is necessary 
# because charging is a critical function and we don't want to wake up to a 
# car that's not ready to go.
#
# author: mjhwa@yahoo.com
##
def chargeMXBackup():
  try:
    # add check to see if car is already charging or do nothing else since 
    # sending a charge command while it's charging doesn't do anything.
    chargeVehicle(MX_VIN)
  except Exception as e:
    logError('chargeMXBackup(): ' + str(e))
    wakeVehicle(MX_VIN)
    time.sleep(WAIT_TIME)
    chargeMXBackup()


def main():
  chargeMXBackup()

if __name__ == "__main__":
  main()
