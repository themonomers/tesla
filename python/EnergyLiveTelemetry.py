from Influxdb import getDBClient
from TeslaEnergyAPI import getSiteLiveStatus
from Logger import logError


##
# Writes live energy data to InfluxDB from the Tesla API.  
#
# author: mjhwa@yahoo.com
##
def writeLiveSiteTelemetry():
  try:
    # get battery data
    data = getSiteLiveStatus()  
    
    json_body = []
    json_body.append({
      'measurement': 'energy_live',
      'tags': {
        'source': 'solar_power'
      },
      'time': data['response']['timestamp'],
      'fields': {
        'value': float(data['response']['solar_power'])
      }
    })

    json_body.append({
      'measurement': 'energy_live',
      'tags': {
        'source': 'battery_power'
      },
      'time': data['response']['timestamp'],
      'fields': {
        'value': float(data['response']['battery_power'])
      }
    })

    json_body.append({
      'measurement': 'energy_live',
      'tags': {
        'source': 'grid_power'
      },
      'time': data['response']['timestamp'],
      'fields': {
        'value': float(data['response']['grid_power'])
      }
    })

    json_body.append({
      'measurement': 'energy_live',
      'tags': {
        'source': 'load_power'
      },
      'time': data['response']['timestamp'],
      'fields': {
        'value': float(data['response']['load_power'])
      }
    })

    json_body.append({
      'measurement': 'energy_live',
      'tags': {
        'source': 'percentage_charged'
      },
      'time': data['response']['timestamp'],
      'fields': {
        'value': float(data['response']['percentage_charged'])
      }
    })

    # Write to Influxdb
    client = getDBClient()
    client.switch_database('live')
    client.write_points(json_body)
    client.close()
  except Exception as e:
    logError('writeLiveSiteTelemetry(): ' + str(e))


##
# Set on a 5 minute interval in crontab.
#
# author: mjhwa@yahoo.com
##
def main():
  writeLiveSiteTelemetry()

if __name__ == "__main__":
  main()

