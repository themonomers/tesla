import pytz
import zoneinfo

from TeslaEnergyAPI import getBatteryChargeHistory, getBatteryBackupHistory
from EnergyTelemetry import writeEnergySummaryToDB, writeEnergyTOUSummaryToGsheet, writeEnergyTOUSummaryToDB, writeEnergyDetailToDB
from Influxdb import getDBClient
from GoogleAPI import getGoogleSheetService
from Utilities import getConfig
from Logger import logError
from datetime import datetime, timedelta

ENERGY_SPREADSHEET_ID = getConfig()['google']['energy_spreadsheet_id']

TIME_ZONE = 'America/Los_Angeles'
PAC = zoneinfo.ZoneInfo(TIME_ZONE)


##
# Import Tesla energy export from the mobile app pasted into a Google Sheet
# into an InfluxDB for Grafana visualization.
#
# author: mjhwa@yahoo.com
##
def importEnergyDetailFromGsheetToDB():
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
    logError('importEnergyDetailFromGsheetToDB(): ' + str(e))


##
# Import Tesla summary energy data from the a Google Sheet into an InfluxDB 
# for Grafana visualization.
#
# author: mjhwa@yahoo.com
##
def importEnergySummaryFromGsheetToDB():
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
              'time': datetime(
                date.year,
                date.month,
                date.day,
                date.hour,
                date.minute,
                date.second,
                date.microsecond
              ).replace(tzinfo=PAC),
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
    logError('importEnergySummaryFromGsheetToDB(): ' + str(e))


##
# Import Tesla battery charge state history into an InfluxDB for 
# Grafana visualization.  These are in 15 minute increments.
#
# author: mjhwa@yahoo.com
##
def importBatteryChargeToDB(date):
  try:
    # get battery charge history data
    data = getBatteryChargeHistory('day', date)

    json_body = []
    dt = ''
    soe = ''
    insert = ''
    for x in data['response']['time_series']:
      for key, value in x.items():
        print(key + ' = ' + str(value))
      
        if key == 'timestamp':
          dt = value
        elif key == 'soe':
          soe = value

          insert = input('import (y/n): ')
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
    logError('importBatteryChargeToDB(): ' + str(e))


##
# Import Tesla system backup history/grid outages into an InfluxDB for
# Grafana visualization.
#
# author: mjhwa@yahoo.com
##
def importOutageToDB():
  try:
    # get battery charge history data
    data = getBatteryBackupHistory()

    json_body = []
    insert = ''

    for i in range(len(data['response']['events'])):
      print(str(i))
      duration = -1
      start = ''

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

        if ((duration != -1) and (start != '')):
          end = start + timedelta(hours=duration)
          print('  end = '
                + datetime.strftime(end, '%Y-%m-%d %I:%M:%S %p'))

          insert = input('import (y/n): ')
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
    logError('importOutageToDB(): ' + str(e))


##
# Import missing dates for Tesla Energy data for InfluxDB.  This
# has 5 minute increments of Home, Solar, Powerall, and Grid to/from
# data.
#
# author: mjhwa@yahoo.com
##
def importEnergyDetailToDB(date):
  try:
    print(date)

    insert = input('import (y/n): ')
    if insert != 'y':
      return

    writeEnergyDetailToDB(date)
  except Exception as e:
    logError('importEnergyDetailToDB(): ' + str(e))


##
# Import missing dates for Tesla Energy data for InfluxDB.  This
# has daily totals of Home, Solar, Powerall, and Grid to/from
# data.
#
# author: mjhwa@yahoo.com
##
def importEnergySummaryToDB(date):
  try:
    print(date)

    insert = input('import (y/n): ')
    if insert != 'y':
      return

    writeEnergySummaryToDB(date)
  except Exception as e:
    logError('importEnergySummaryToDB(): ' + str(e))


##
# Import missing dates for Tesla Energy Impact data for Google Sheet.
# This includes TOU (off peak, partial peak, and peak) breakdowns
# of Solar, Powerall, Grid, etc., Energy Value, and Solar Offset.
#
# author: mjhwa@yahoo.com
##
def importEnergyTOUSummaryToGsheet(date):
  try:
    print(date)

    insert = input('import (y/n): ')
    if insert != 'y':
      return

    writeEnergyTOUSummaryToGsheet(date)
  except Exception as e:
    logError('importEnergyTOUSummaryToGsheet(): ' + str(e))


##
# Import missing dates for Tesla Energy Impact data for InfluxDB.
# This includes TOU (off peak, partial peak, and peak) breakdowns
# of Solar, Powerall, Grid, etc., Energy Value, and Solar Offset.
#
# author: mjhwa@yahoo.com
##
def importEnergyTOUSummaryToDB(date):
  try:
    print(date)

    insert = input('import (y/n): ')
    if insert != 'y':
      return

    writeEnergyTOUSummaryToDB(date)
  except Exception as e:
    logError('importEnergyTOUSummaryToDB(): ' + str(e))


##
# Collection of data import functions run from CLI python 
# to manually run automated data collection routines that 
# failed.
#
# author: mjhwa@yahoo.com
##
def main():
  print('[1] importEnergyDetailFromGsheetToDB()')
  print('[2] importEnergySummaryFromGsheetToDB()')
  print('[3] importBatteryChargeToDB()')
  print('[4] importOutageToDB()')
  print('[5] importEnergyDetailToDB()')
  print('[6] importEnergySummaryToDB()')
  print('[7] importEnergyTOUSummaryToGsheet()')
  print('[8] importEnergyTOUSummaryToDB()')
  try:
    choice = int(input('selection: '))
  except ValueError:
    return

  if choice == 1:
    importEnergyDetailFromGsheetToDB()
  elif choice == 2:
    importEnergySummaryFromGsheetToDB()
  elif choice == 3:
    date = input('date(m/d/yyyy): ')
    date = datetime.strptime(date, '%m/%d/%Y')
    importBatteryChargeToDB(date)
  elif choice == 4:
    importOutageToDB()
  elif choice == 5:
    date = input('date(m/d/yyyy): ')
    date = datetime.strptime(date, '%m/%d/%Y')
    importEnergyDetailToDB(date)
  elif choice == 6:
    date = input('date(m/d/yyyy): ')
    date = datetime.strptime(date, '%m/%d/%Y')
    importEnergySummaryToDB(date)
  elif choice == 7:
    date = input('date(m/d/yyyy): ')
    date = datetime.strptime(date, '%m/%d/%Y')
    importEnergyTOUSummaryToGsheet(date)
  elif choice == 8:
    date = input('date(m/d/yyyy): ')
    date = datetime.strptime(date, '%m/%d/%Y')
    importEnergyTOUSummaryToDB(date)


if __name__ == "__main__":
  main()

