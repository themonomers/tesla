import configparser
import os

from influxdb import InfluxDBClient
from Crypto import decrypt
from Logger import logError
from io import StringIO

buffer = StringIO(
  decrypt(
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
INFLUX_HOST = config['influxdb']['host']
INFLUX_PORT = config['influxdb']['port']
INFLUX_USER = config['influxdb']['user']
INFLUX_PASSWORD = config['influxdb']['password']
buffer.close()


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


