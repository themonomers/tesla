import pytz
import zoneinfo
import argparse

from energy.api import get_battery_backup_history
from energy.telemetry import (
  write_energy_summary_to_db, 
  write_energy_data_to_gsheet, 
  write_energy_tou_summary_to_db, 
  write_energy_detail_to_db, 
  write_battery_charge_to_db
)
from common.utilities import get_config, NewlineFormatter
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

    insert = input('import detail_to_db (y/N): ')
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

    insert = input('import summary_to_db (y/N): ')
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

    insert = input('import tou_summary_to_db (y/N): ')
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

    insert = input('import data_to_gsheet (y/N): ')
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

    insert = input('import battery_charge_to_db (y/N): ')
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
          insert = input('import outage_to_db (y/N): ')
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
# Collection of data import functions run from CLI python 
# to manually run automated data collection routines that 
# failed.
#
# author: mjhwa@yahoo.com
##
def main(parser):
  args = parser.parse_args()

  if not any(vars(args).values()):
    parser.print_help()
    return

  if ((args.detail_to_db or 
       args.summary_to_db or 
       args.tou_summary_to_db or
       args.data_to_gsheet or
       args.battery_charge_to_db) and 
       not args.date):
    parser.error('--date (m/d/yyyy) is required when --detail_to_db, --summary_to_db, --tou_summary_to_db, '
                 '--data_to_gsheet, or --battery_charge_to_db is used')

  date = None
  if (args.date):
    date = datetime.strptime(args.date[0].strftime('%m/%d/%Y'), '%m/%d/%Y') 

  if (args.detail_to_db):
    import_energy_detail_to_db(date)
  
  if (args.summary_to_db):
    import_energy_summary_to_db(date)

  if (args.tou_summary_to_db):
    import_energy_tou_summary_to_db(date)

  if (args.data_to_gsheet):
    import_energy_data_to_gsheet(date)

  if (args.battery_charge_to_db):
    import_battery_charge_to_db(date)

  if (args.outage_to_db):
    import_outage_to_db()


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
                    prog='import.py',
                    description='Imports data manually when automated processes fail.',
                    formatter_class=lambda prog: NewlineFormatter(prog, 
                                                                  indent_increment=2, 
                                                                  max_help_position=30, 
                                                                  width=80))
  parser.add_argument(
#                      '-e', 
                      '--detail_to_db', 
                      help='writes energy data to InfluxDB in 5 minute increments for Home, Solar, Powerall, and Grid',
                      action='store_true'
                     )
  parser.add_argument(
#                      '-s', 
                      '--summary_to_db', 
                      help='writes energy data to InfluxDB of daily totals for Home, Solar, Powerall, and Grid',
                      action='store_true'
                     )
  parser.add_argument(
#                      '-t', 
                      '--tou_summary_to_db', 
                      help='writes energy data to InfluxDB of TOU (off peak, partial peak, and peak) breakdowns of '
                           'Solar, Powerall, Grid, etc., Energy Value, and Solar Offset',
                      action='store_true'
                     )
  parser.add_argument(
#                      '-g', 
                      '--data_to_gsheet', 
                      help='writes energy data to Google Sheet of TOU (off peak, partial peak, and peak) breakdowns of '
                           'Solar, Powerall, Grid, etc., Energy Value, and Solar Offset',
                      action='store_true'
                     )
  parser.add_argument(
#                      '-b', 
                      '--battery_charge_to_db', 
                      help='writes battery charge state history to InfluxDB in 15 minute increments',
                      action='store_true'
                     )
  parser.add_argument(
#                      '-o', 
                      '--outage_to_db', 
                      help='writes system backup history/grid outages to InfluxDB',
                      action='store_true'
                     )
  parser.add_argument(
#                      '-d', 
                      '--date', 
                      help='date of data import in m/d/yyyy format',
                      type=lambda d: datetime.strptime(d, '%m/%d/%Y'),
                      nargs=1,
                      metavar='date'
                     )

  main(parser)