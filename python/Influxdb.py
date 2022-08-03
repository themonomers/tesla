from Utilities import getConfig
from Logger import logError
from influxdb import InfluxDBClient

config = getConfig()
INFLUX_HOST = config['influxdb']['host']
INFLUX_PORT = config['influxdb']['port']
INFLUX_USER = config['influxdb']['user']
INFLUX_PASSWORD = config['influxdb']['password']


##
# Gets a connection to an instance of InfluxDB.
#
# author: mjhwa@yahoo.com
##
def getDBClient():
  try:
    return InfluxDBClient(
      host=INFLUX_HOST, 
      port=INFLUX_PORT, 
      username=INFLUX_USER, 
      password=INFLUX_PASSWORD
    )
  except Exception as e:
    logError('getDBClient(): ' + str(e))


