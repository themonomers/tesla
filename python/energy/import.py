import pytz
import zoneinfo

from energy.api import get_battery_backup_history
from energy.telemetry import write_energy_summary_to_db, write_energy_data_to_gsheet, write_energy_tou_summary_to_db, write_energy_detail_to_db, write_battery_charge_to_db
from common.googleutil import get_google_sheet_service
from common.utilities import get_config
from common.influxdb import get_db_client
from common.logger import log_error
from datetime import datetime

config = get_config()
ENERGY_SPREADSHEET_ID = config['google']['energy_spreadsheet_id']

TIME_ZONE = config['general']['timezone']
PAC = zoneinfo.ZoneInfo(TIME_ZONE)


##
# Import missing dates for Tesla Energy data for InfluxDB.  This
# has 5 minute increments of Home, Solar, Powerall, and Grid to/from
# data.
#
# author: mjhwa@yahoo.com
##
def import_energy_detail_to_db(date):
  try:
    print(date)

    insert = input('import (y/N): ')
    if insert != 'y':
      return

    write_energy_detail_to_db(date)
  except Exception as e:
    log_error('import_energy_detail_to_db():', e)


##
# Import missing dates for Tesla Energy data for InfluxDB.  This
# has daily totals of Home, Solar, Powerall, and Grid to/from
# data.
#
# author: mjhwa@yahoo.com
##
def import_energy_summary_to_db(date):
  try:
    print(date)

    insert = input('import (y/N): ')
    if insert != 'y':
      return

    write_energy_summary_to_db(date)
  except Exception as e:
    log_error('import_energy_summary_to_db():', e)


##
# Import missing dates for Tesla Energy Impact data for InfluxDB.
# This includes TOU (off peak, partial peak, and peak) breakdowns
# of Solar, Powerall, Grid, etc., Energy Value, and Solar Offset.
#
# author: mjhwa@yahoo.com
##
def import_energy_tou_summary_to_db(date):
  try:
    print(date)

    insert = input('import (y/N): ')
    if insert != 'y':
      return

    write_energy_tou_summary_to_db(date)
  except Exception as e:
    log_error('import_energy_tou_summary_to_db():', e)


##
# Import missing dates for Tesla Energy Impact data for Google Sheet.
# This includes TOU (off peak, partial peak, and peak) breakdowns
# of Solar, Powerall, Grid, etc., Energy Value, and Solar Offset.
#
# author: mjhwa@yahoo.com
##
def import_energy_data_to_gsheet(date):
  try:
    print(date)

    insert = input('import (y/N): ')
    if insert != 'y':
      return

    write_energy_data_to_gsheet(date)
  except Exception as e:
    log_error('import_energy_data_to_gsheet():', e)


##
# Import Tesla battery charge state history into an InfluxDB for 
# Grafana visualization.  These are in 15 minute increments.
#
# author: mjhwa@yahoo.com
##
def import_battery_charge_to_db(date):
  try:
    print(date)

    insert = input('import (y/N): ')
    if insert != 'y':
      return

    write_battery_charge_to_db(date)
  except Exception as e:
    log_error('import_battery_charge_to_db():', e)


##
# Import Tesla system backup history/grid outages into an InfluxDB for
# Grafana visualization.
#
# author: mjhwa@yahoo.com
##
def import_outage_to_db():
  try:
    # get battery backup history data
    data = get_battery_backup_history()

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
          insert = input('import (y/N): ')
          if insert != 'y':
            break

          json_body.append({
            'measurement': 'backup',
            'tags': {
              'source': 'event'
            },
            'time': start,
            'fields': {
              'value': float(duration)
            }
          })

    # Write to Influxdb
    client = get_db_client()
    client.switch_database('outage')
    client.write_points(json_body)
    client.close()
  except Exception as e:
    log_error('import_outage_to_db():', e)


##
# Import Tesla energy export from the mobile app pasted into a Google Sheet
# into an InfluxDB for Grafana visualization.
#
# author: mjhwa@yahoo.com
##
def import_energy_detail_from_gsheet_to_db():
  try:
    # get time series data
    service = get_google_sheet_service()
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
    client = get_db_client()
    client.switch_database('energy')
    client.write_points(json_body)
    client.close()
  except Exception as e:
    log_error('import_energy_detail_from_gsheet_to_db():', e)


##
# Import Tesla summary energy data from the a Google Sheet into an InfluxDB 
# for Grafana visualization.
#
# author: mjhwa@yahoo.com
##
def import_energy_summary_from_gsheet_to_db():
  try:
    # get time series data
    service = get_google_sheet_service()
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
    client = get_db_client()
    client.switch_database('energy')
    client.write_points(json_body)
    client.close()
  except Exception as e:
    log_error('import_energy_summary_from_gsheet_to_db():', e)


##
# Collection of data import functions run from CLI python 
# to manually run automated data collection routines that 
# failed.
#
# author: mjhwa@yahoo.com
##
def main():
  print('[1] import_energy_detail_to_db()')
  print('[2] import_energy_summary_to_db()')
  print('[3] import_energy_tou_summary_to_db()')
  print('[4] import_energy_data_to_gsheet()')
  print('[5] import_battery_charge_to_db()')
  print('[6] import_outage_to_db()')
#  print('[7] import_energy_detail_from_gsheet_to_db()')
#  print('[8] import_energy_summary_from_gsheet_to_db()')
  try:
    choice = int(input('selection: '))
  except ValueError:
    return

  if choice == 1:
    date = input('date(m/d/yyyy): ')
    date = datetime.strptime(date, '%m/%d/%Y')
    import_energy_detail_to_db(date)
  elif choice == 2:
    date = input('date(m/d/yyyy): ')
    date = datetime.strptime(date, '%m/%d/%Y')
    import_energy_summary_to_db(date)
  elif choice == 3:
    date = input('date(m/d/yyyy): ')
    date = datetime.strptime(date, '%m/%d/%Y')
    import_energy_tou_summary_to_db(date)
  elif choice == 4:
    date = input('date(m/d/yyyy): ')
    date = datetime.strptime(date, '%m/%d/%Y')
    import_energy_data_to_gsheet(date)
  elif choice == 5:
    date = input('date(m/d/yyyy): ')
    date = datetime.strptime(date, '%m/%d/%Y')
    import_battery_charge_to_db(date)
  elif choice == 6:
    import_outage_to_db()
#  elif choice == 7:
#    import_energy_detail_from_gsheet_to_db()
#  elif choice == 8:
#    import_energy_summary_from_gsheet_to_db()


if __name__ == "__main__":
  main()

