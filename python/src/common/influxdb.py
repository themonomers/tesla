from common.configutil import encrypted_config
from influxdb import InfluxDBClient


##
# Gets a connection to an instance of InfluxDB.
#
# author: mjhwa@yahoo.com
##
def get_db_client():
  return InfluxDBClient(
    host=encrypted_config['influxdb']['host'], 
    port=encrypted_config['influxdb']['port'], 
    username=encrypted_config['influxdb']['user'], 
    password=encrypted_config['influxdb']['password']
  )