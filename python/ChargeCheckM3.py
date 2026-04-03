from TeslaVehicleAPI import getVehicleData, startChargeVehicle
from Utilities import getConfig, isVehicleAtPrimary
from Logger import logError, logMessage
from datetime import datetime

config = getConfig()
M3_VIN = config['vehicle']['m3_vin']


##
# Additional scheduled charging check run on crontab.  If it failed to start, this
# will attempt to start it at the target time.
#
# author: mjhwa@yahoo.com
def chargeCheckM3():
  try:
    m3_data = getVehicleData(M3_VIN)

    if (isVehicleAtPrimary(m3_data) and 
        (m3_data['response']['charge_state']['charging_state'] != 'Charging')):
      logMessage('chargeCheckM3(): Scheduled charging failed to start.  Starting backup charging.')
      startChargeVehicle(M3_VIN)
  except Exception as e:
    logError('chargeCheckM3(): ' + str(e))

def main():
  chargeCheckM3()

if __name__ == "__main__":
  main()