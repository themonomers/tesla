from common.configutil import encrypted_config
from influxdb import InfluxDBClient

INFLUX_HOST = encrypted_config['influxdb']['host']
INFLUX_PORT = encrypted_config['influxdb']['port']
INFLUX_USER = encrypted_config['influxdb']['user']
INFLUX_PASSWORD = encrypted_config['influxdb']['password']


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