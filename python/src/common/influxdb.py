from common.configutil import get_config
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
  return InfluxDBClient(
    host=INFLUX_HOST, 
    port=INFLUX_PORT, 
    username=INFLUX_USER, 
    password=INFLUX_PASSWORD
  )