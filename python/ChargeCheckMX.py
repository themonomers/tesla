from TeslaVehicleAPI import getVehicleData, startChargeVehicle
from Utilities import getConfig, isVehicleAtPrimary
from Logger import logError, logInfo
from datetime import datetime

config = getConfig()
MX_VIN = config['vehicle']['mx_vin']


##
# Additional scheduled charging check run on crontab.  If it failed to start, this
# will attempt to start it at the target time.
#
# author: mjhwa@yahoo.com
def chargeCheckMX():
  try:
    mx_data = getVehicleData(MX_VIN)

    if (isVehicleAtPrimary(mx_data) and 
        (mx_data['response']['charge_state']['charging_state'] != 'Charging')):
      logInfo('chargeCheckMX(): Scheduled charging failed to start.  Starting backup charging.')
      startChargeVehicle(MX_VIN)
  except Exception as e:
    logError('chargeCheckMX(): ' + str(e))

def main():
  chargeCheckMX()

if __name__ == "__main__":
  main()