import time
import configparser
import os
import tzlocal
import pytz

from TeslaEnergyAPI import getBatteryChargeHistory, getBatteryBackupHistory
from EnergyTelemetry import writeSiteTelemetrySummary, writeSiteTelemetryTOUSummary, writeSiteTelemetryTOUSummaryDB
from Influxdb import getDBClient
from GoogleAPI import getGoogleSheetService
from Crypto import decrypt
from Logger import logError
from datetime import datetime, timedelta
from io import StringIO

buffer = StringIO(
  decrypt(
    os.path.join(
      os.path.dirname(os.path.abspath(__file__)),
      'config.rsa'
    )
  ).decode('utf-8')
)
config = configparser.ConfigParser()
config.sections()
config.readfp(buffer)
ENERGY_SPREADSHEET_ID = config['google']['energy_spreadsheet_id']
buffer.close()

TIME_ZONE = 'America/Los_Angeles'


##
# Import Tesla energy export from the mobile app pasted into a Google Sheet
# into an InfluxDB for Grafana visualization.
#
# author: mjhwa@yahoo.com
##
def importSiteTelemetryDetail():
  try:
    # get time series data
    service = getGoogleSheetService()
    data = service.spreadsheets().values().get(
      spreadsheetId=ENERGY_SPREADSHEET_ID,
      range='import!A:E'
    ).execute().get('values', [])
    service.close()

    json_body = []
    for x in range(len(data)):
      if (x != 0): 
        json_body.append({
          'measurement': 'energy_detail',
          'tags': {
            'source': 'grid_power'
          },
          'time': data[x][0],
          'fields': {
            'value': float(data[x][4]) * 1000
          }
        })

        json_body.append({
          'measurement': 'energy_detail',
          'tags': {
            'source': 'battery_power'
          },
          'time': data[x][0],
          'fields': {
            'value': float(data[x][3]) * 1000
          }
        })

        json_body.append({
          'measurement': 'energy_detail',
          'tags': {
            'source': 'solar_power'
          },
          'time': data[x][0],
          'fields': {
            'value': float(data[x][2]) * 1000
          }
        })

        json_body.append({
          'measurement': 'energy_detail',
          'tags': {
            'source': 'load_power'
          },
          'time': data[x][0],
          'fields': {
            'value': float(data[x][1]) * 1000
          }
        })

    # Write to Influxdb
    client = getDBClient()
    client.switch_database('energy')
    client.write_points(json_body)
    client.close()
  except Exception as e:
    logError('importSiteTelemetryDetail(): ' + str(e))


##
# Import Tesla summary energy data from the a Google Sheet into an InfluxDB 
# for Grafana visualization.
#
# author: mjhwa@yahoo.com
##
def importSiteTelemetrySummary():
  try:
    # get time series data
    service = getGoogleSheetService()
    data = service.spreadsheets().values().get(
      spreadsheetId=ENERGY_SPREADSHEET_ID,
      range='Telemetry-Summary!A:V'
    ).execute().get('values', [])
    service.close()

    json_body = []
    for x in range(len(data)):
      if ((x != 0) and (x != 1) and (x != 2)):

        for y in range(len(data[x])):
          if ((y != 0) and (y != 3) and (y != 4) and (y !=5) and (y < 19)):

            date = datetime.strptime(data[x][0],'%B %d, %Y')

            json_body.append({
              'measurement': 'energy_summary',
              'tags': {
                'source': data[1][y]
              },
#              'time': datetime.strptime(
#                data[x][0], 
#                '%B %d, %Y'
#              ).strftime('%Y-%m-%dT%H:%M:%S-7:00'),
              'time': tzlocal.get_localzone().localize(datetime(
                date.year,
                date.month,
                date.day,
                date.hour,
                date.minute,
                date.second,
                date.microsecond
              )),
              'fields': {
                'value': float(data[x][y].replace(',',''))
              }
            })

    # Write to Influxdb
    client = getDBClient()
    client.switch_database('energy')
    client.write_points(json_body)
    client.close()
  except Exception as e:
    logError('importSiteTelemetrySummary(): ' + str(e))


##
# Import Tesla battery charge state history into an InfluxDB for 
# Grafana visualization.
#
# author: mjhwa@yahoo.com
##
def importBatteryChargeHistory(date):
  try:
    # get battery charge history data
    data = getBatteryChargeHistory('day', date)

    json_body = []
    dt = ''
    soe = ''
    insert = ''
    for x in data['response']['time_series']:
      for key, value in x.iteritems():
        print(key + ' = ' + str(value))
      
        if key == 'timestamp':
          dt = value
        elif key == 'soe':
          soe = value

          insert = raw_input('import (y/n): ')
          if insert != 'y':
            break

          json_body.append({
            'measurement': 'energy_detail',
            'tags': {
              'source': 'percentage_charged'
            },
            'time': dt,
            'fields': {
              'value': float(soe)
            }
          })

    # Write to Influxdb
    client = getDBClient()
    client.switch_database('energy')
    client.write_points(json_body)
    client.close()
  except Exception as e:
    logError('importBatteryChargeHistory(): ' + str(e))


##
# Import Tesla battery backup history/grid outages into an InfluxDB for
# Grafana visualization.
#
# author: mjhwa@yahoo.com
##
def importBatteryBackupHistory():
  try:
    # get battery charge history data
    data = getBatteryBackupHistory()

    json_body = []
    insert = ''

    for i in range(len(data['response']['events'])):
      print(str(i))

      for key, value in data['response']['events'][i].items():
        if (key == 'duration'):
          duration = float(value) / 1000 / 60 / 60
          print('  ' + key + ' = ' + str(duration) + ' hours')

        if (key == 'timestamp'):
          local = pytz.timezone(TIME_ZONE)

          start = value[0:len(value) - 6:1]
          start = local.localize(
                    datetime.strptime(start, '%Y-%m-%dT%H:%M:%S')
                  , is_dst=None)
          print('  ' + key + ' = '
                + datetime.strftime(start, '%Y-%m-%d %I:%M:%S %p'))

          end = start + timedelta(hours=duration)
          print('  end = '
                + datetime.strftime(end, '%Y-%m-%d %I:%M:%S %p'))

          insert = raw_input('import (y/n): ')
          if insert != 'y':
            break

          json_body.append({
            'measurement': 'backup',
            'tags': {
              'source': 'event'
            },
            'time': str(start.astimezone(pytz.utc)),
            'fields': {
              'value': duration
            }
          })

          json_body.append({
            'measurement': 'backup',
            'tags': {
              'source': 'event'
            },
            'time': str(end.astimezone(pytz.utc)),
            'fields': {
              'value': duration
            }
          })

    # Write to Influxdb
    client = getDBClient()
    client.switch_database('outage')
    client.write_points(json_body)
    client.close()
  except Exception as e:
    logError('importBatteryBackupHistory(): ' + str(e))


##
# Import missing dates for Tesla site telemetry summary.
#
# author: mjhwa@yahoo.com
##
def importSiteTelemetrySummary(date):
  try:
    print(date)

    insert = raw_input('import (y/n): ')
    if insert != 'y':
      return

    writeSiteTelemetrySummary(date)
  except Exception as e:
    logError('importSiteTelemetrySummary(): ' + str(e))


##
# Import missing dates for Tesla site telemetry TOU summary.
#
# author: mjhwa@yahoo.com
##
def importSiteTelemetryTOUSummary(date):
  try:
    print(date)

    insert = raw_input('import (y/n): ')
    if insert != 'y':
      return

    writeSiteTelemetryTOUSummary(date)
  except Exception as e:
    logError('importSiteTelemetryTOUSummary(): ' + str(e))


# Import missing dates for Tesla site telemetry TOU summary for InfluxDB.
#
# author: mjhwa@yahoo.com
##
def importSiteTelemetryTOUSummaryDB(date):
  try:
    print(date)

    insert = raw_input('import (y/n): ')
    if insert != 'y':
      return

    writeSiteTelemetryTOUSummaryDB(date)
  except Exception as e:
    logError('importSiteTelemetryTOUSummaryDB(): ' + str(e))


def main():
  print('[1] importSiteTelemetryDetail()')
  print('[2] importSiteTelemetrySummary()')
  print('[3] importBatteryChargeHistory()')
  print('[4] importBatteryBackupHistory()')
  print('[5] importSiteTelemetrySummary()')
  print('[6] importSiteTelemetryTOUSummary()')
  print('[7] importSiteTelemetryTOUSummaryDB() \n')
  try:
    choice = int(raw_input('selection: '))
  except ValueError:
    return

  if choice == 1:
    importSiteTelemetryDetail()
  elif choice == 2:
    importSiteTelemetrySummary()
  elif choice == 3:
    date = raw_input('date(m/d/yyyy): ')
    date = datetime.strptime(date, '%m/%d/%Y')
    importBatteryChargeHistory(date)
  elif choice == 4:
    importBatteryBackupHistory()
  elif choice == 5:
    date = raw_input('date(m/d/yyyy): ')
    date = datetime.strptime(date, '%m/%d/%Y')
    importSiteTelemetrySummary(date)
  elif choice == 6:
    date = raw_input('date(m/d/yyyy): ')
    date = datetime.strptime(date, '%m/%d/%Y')
    importSiteTelemetryTOUSummary(date)
  elif choice == 7:
    date = raw_input('date(m/d/yyyy): ')
    date = datetime.strptime(date, '%m/%d/%Y')
    importSiteTelemetryTOUSummaryDB(date)

if __name__ == "__main__":
  main()

