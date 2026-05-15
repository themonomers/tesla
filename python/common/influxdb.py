from common.utilities import get_config, log
from influxdb import InfluxDBClient

config = get_config()
INFLUX_HOST = config['influxdb']['host']
INFLUX_PORT = config['influxdb']['port']
INFLUX_USER = config['influxdb']['user']
INFLUX_PASSWORD = config['influxdb']['password']


##
# Gets a connection to an instance of InfluxDB.
#
# author: mjhwa@yahoo.com
##
def get_db_client():
  try:
    return InfluxDBClient(
      host=INFLUX_HOST, 
      port=INFLUX_PORT, 
      username=INFLUX_USER, 
      password=INFLUX_PASSWORD
    )
  except Exception as e:
    log().error('get_db_client(): ' + str(e))


