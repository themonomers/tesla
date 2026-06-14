import json
import pytz
import argparse

from common.configutil import get_config
from common.argutil import CustomHelpFormatter
from common.utilities import print_json, send_request
from common.tokenutil import get_token
from common.fileutil import get_filepath
from datetime import datetime

ACCESS_TOKEN = get_token()['tesla']['access_token']

config = get_config()
SITE_ID = config['energy']['site_id']
BASE_PROXY_URL = config['tesla']['base_proxy_url']
TIME_ZONE = config['general']['timezone']
CERT = get_filepath('secrets', 'teslaCert')

##
# Gets some quick and basic information.
#
# author: mjhwa@yahoo.com
##
def get_site_status():
  return json.loads(
    send_get(get_url('site_status')).text
  )


##
# Gets more information as well as live data such as solar production.
#
# author: mjhwa@yahoo.com
##
def get_site_live_status():
  return json.loads(
    send_get(get_url('live_status')).text
  )


##
# Gets detailed information.
#
# author: mjhwa@yahoo.com
##
def get_site_info():
  return json.loads(
    send_get(get_url('site_info')).text
  )


##
# Gets summary level information about energy imports and exports down to the
# day.
#
# author: mjhwa@yahoo.com
##
def get_site_history(period, date):
  local = pytz.timezone(TIME_ZONE)
  date = local.localize(datetime(
    date.year, 
    date.month, 
    date.day, 
    23, 
    59, 
    59, 
    0
  ), is_dst=None)

  command = ('calendar_history'
              + '?kind=energy'
              + '&end_date=' 
              + datetime.strftime(date.astimezone(pytz.utc), '%Y-%m-%dT%H:%M:%SZ')
              + '&period=' + period)

  return json.loads(
    send_get(get_url(command)).text
  )


##
# Get grid outage/battery backup events.
#
# author: mjhwa@yahoo.com
##
def get_battery_backup_history():
  return json.loads(
    send_get(get_url('calendar_history?kind=backup')).text
  )


##
# Gets summary level information about energy imports and exports down to the
# day, separated by time of use.
#
# author: mjhwa@yahoo.com
##
def get_site_tou_history(period, date):
  local = pytz.timezone(TIME_ZONE)
  s_date = local.localize(datetime(
    date.year,
    date.month,
    date.day,
    0,
    0,
    0,
    0
  ), is_dst=None)

  e_date = local.localize(datetime(
    date.year,
    date.month,
    date.day,
    23,
    59,
    59,
    0
  ), is_dst=None)

  command = ('calendar_history'
              + '?kind=time_of_use_energy'
              + '&period=' + period
              + '&start_date=' 
              + datetime.strftime(
                s_date.astimezone(pytz.utc), 
                '%Y-%m-%dT%H:%M:%SZ')
              + '&end_date=' 
              + datetime.strftime(
                e_date.astimezone(pytz.utc), 
                '%Y-%m-%dT%H:%M:%SZ'))

  return json.loads(
    send_get(get_url(command)).text
  )


##
# Gets the historic battery charge level data in 15 minute increments that's
# shown on the mobile app. 
#
# author: mjhwa@yahoo.com
##
def get_battery_charge_history(period, date):
  local = pytz.timezone(TIME_ZONE)
  date = local.localize(datetime(
    date.year,
    date.month,
    date.day,
    23,
    59,
    59,
    0
  ), is_dst=None)

  command = ('calendar_history'
              + '?kind=soe'
              + '&period=' + period
              + '&end_date='
              + datetime.strftime(date.astimezone(pytz.utc), '%Y-%m-%dT%H:%M:%SZ'))

  return json.loads(
    send_get(get_url(command)).text
  )


##
# Gets energy information in 5 minute increments, with ability to query by 
# date.  Used to create the "ENERGY USAGE" charts in the mobile app.
#
# author: mjhwa@yahoo.com
##
def get_power_history(period, date):
  local = pytz.timezone(TIME_ZONE)
  s_date = local.localize(datetime(
    date.year,
    date.month,
    date.day,
    0,
    0,
    0,
    0
  ), is_dst=None)

  e_date = local.localize(datetime(
    date.year,
    date.month,
    date.day,
    23,
    59,
    59,
    0
  ), is_dst=None)

  command = ('calendar_history'
              + '?kind=power'
              + '&start_date='
              + datetime.strftime(
                s_date.astimezone(pytz.utc), 
                '%Y-%m-%dT%H:%M:%SZ')
              + '&end_date='
              + datetime.strftime(
                e_date.astimezone(pytz.utc), 
                '%Y-%m-%dT%H:%M:%SZ')
              + '&period=' + period)

  return json.loads(
    send_get(get_url(command)).text
  )


##
# Lists all rate tariffs available in the mobile app.
#
# author: mjhwa@yahoo.com
##
def get_rate_tariffs():
  url = (BASE_PROXY_URL
          + '/energy_sites/' 
          + 'rate_tariffs')

  return json.loads(
    send_get(url).text
  )


##
# Lists the tariff selected for your site in the mobile
# app along with published rates, TOU schedules, etc.
#
# author: mjhwa@yahoo.com
##
def get_site_tariff():
  return json.loads(
    send_get(get_url('tariff_rate')).text
  )


##
# Retrieves the estimated time remaining in the powerwall(s).
#
# author: mjhwa@yahoo.com
##
def get_backup_time_remaining():
  return json.loads(
    send_get(get_url('backup_time_remaining')).text
  )


##
# Gets the data for Solar Value in the mobile app to show estimated 
# cost savings.  
#
# author: mjhwa@yahoo.com
##
def get_savings_forecast(period, date):
  local = pytz.timezone(TIME_ZONE)
  s_date = local.localize(datetime(
    date.year,
    date.month,
    date.day,
    0,
    0,
    0,
    0
  ), is_dst=None)

  e_date = local.localize(datetime(
    date.year,
    date.month,
    date.day,
    23,
    59,
    59,
    0
  ), is_dst=None)

  command = ('calendar_history'
              + '?kind=savings'
              + '&period=' + period
              + '&start_date=' 
              + datetime.strftime(
                s_date.astimezone(pytz.utc),
                '%Y-%m-%dT%H:%M:%SZ')
              + '&end_date=' 
              + datetime.strftime(
                e_date.astimezone(pytz.utc),
                '%Y-%m-%dT%H:%M:%SZ')
              + '&tariff=PGE-EV2-A')

  return json.loads(
    send_get(get_url(command)).text
  )


##
# Changes Operational Mode in the mobile app to "Backup-only".
# This doesn't appear to be any setting in the mobile app
# but this API call still forces the system to only use the 
# battery in an outage.  This also has a side effect of hiding
# the Time of Use card as well as returns an empty response
# when calling the API for Time of Use data.
#
# author: mjhwa@yahoo.com
##
def set_operational_mode_backup():
  return set_operational_mode('backup')


##
# Changes Operational Mode in the mobile app to "Self-Powered".
#
# author: mjhwa@yahoo.com
##
def set_operational_mode_self_powered():
  return set_operational_mode('self_consumption')


##
# Changes Operational Mode in the mobile app to "Time-Based Control".
#
# author: mjhwa@yahoo.com
##
def set_operational_mode_time_based_control():
  return set_operational_mode('autonomous')


##
# Changes Operational Mode setting in the mobile app. 
#
# author: mjhwa@yahoo.com
##
def set_operational_mode(mode):
  payload = {
    'default_real_mode': mode
  }

  return send_post(get_url('operation'), payload)


##
# Changes Energy Exports in the mobile app to "Everything".
# Defaults Grid Charging setting to "No".
#
# author: mjhwa@yahoo.com
##
def set_energy_exports_everything():
  return set_grid_import_export('battery_ok', True)


##
# Changes Energy Exports in the mobile app to "Solar".
# Defaults Grid Charging setting to "No".
#
# author: mjhwa@yahoo.com
##
def set_energy_exports_solar():
  return set_grid_import_export('pv_only', True)


##
# Changes Energy Exports and Grid Charging settings in the mobile app.
#
# author: mjhwa@yahoo.com
##
def set_grid_import_export(export_rule, disallow_grid_charging):
  payload = {
    'customer_preferred_export_rule': export_rule,
    'disallow_charge_from_grid_with_solar_installed': disallow_grid_charging
  }

  return send_post(get_url('grid_import_export'), payload)


##
# Sets "Reserve Energy for Grid Outages", % Backup, in the mobile app.
#
# author: mjhwa@yahoo.com
##
def set_backup_reserve(backup_percent):
  payload = {
    'backup_reserve_percent': backup_percent
  }

  return send_post(get_url('backup'), payload)


##
# Sets off grid vehicle charging reserve % to save for home use.
# It seems the maximum is 95% so 5% is the minimum to share with vehicle.
#
# author: mjhwa@yahoo.com
##
def set_off_grid_vehicle_charging_reserve(percent):
  payload = {
    'off_grid_vehicle_charging_reserve_percent': percent
  }

  return send_post(get_url('off_grid_vehicle_charging_reserve'), payload)


###
# Centralize repetitive URL construction.
#
# author: mjhwa@yahoo.com
##
def get_url(command):
  return (BASE_PROXY_URL
          + '/energy_sites/' 
          + SITE_ID 
          + '/'
          + command)


def send_get(url):
  return send_request('GET', url, ACCESS_TOKEN, None, CERT)


def send_post(url, payload):
  return send_request('POST', url, ACCESS_TOKEN, payload, CERT)


def main(parser):
  args = parser.parse_args()

  if ((args.site_history or 
       args.site_tou_history or
       args.battery_charge_history or
       args.power_history or
       args.savings_forecast) and 
       not args.date):
    parser.error('--date (m/d/yyyy) is required when --site_history, --site_tou_history, --battery_charge_history, '
                 '--power_history, or --savings_forecast is used')

  date = None
  if (args.date):
    date = datetime.strptime(args.date[0].strftime('%m/%d/%Y'), '%m/%d/%Y') 

  data = {}
  if (args.site_status):
    data = get_site_status()
  elif (args.site_live_status):
    data = get_site_live_status()
  elif (args.site_info):
    data = get_site_info()
  elif (args.battery_backup_history):
    data = get_battery_backup_history()
  elif (args.backup_time_remaining):
    data = get_backup_time_remaining()
  elif (args.site_tariff):
    data = get_site_tariff()
  elif (args.site_history):
    data = get_site_history('day', date)
  elif (args.site_tou_history):
    data = get_site_tou_history('day', date)
  elif (args.battery_charge_history):
    data = get_battery_charge_history('day', date)
  elif (args.power_history):
    data = get_power_history('day', date)
  elif (args.savings_forecast):
    data = get_savings_forecast('day', date)
  else:
    parser.print_help()

  print_json(data, 0)


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
                    prog='api.py',
                    description='API calls for Tesla Energy products.',
                    formatter_class=CustomHelpFormatter)
  group = parser.add_mutually_exclusive_group()
  group.add_argument(
                     '-s', 
                     '--site_status', 
                     help='prints site summary information, e.g. Gateway ID',
                     action='store_true'
                    )
  group.add_argument(
                     '-l', 
                     '--site_live_status', 
                     help='prints live data of load, grid, solar, battery, etc.',
                     action='store_true'
                    )
  group.add_argument(
                     '-i', 
                     '--site_info', 
                     help='prints site configuration and setting details',
                     action='store_true'
                    )
  group.add_argument(
                     '-b', 
                     '--battery_backup_history', 
                     help='prints grid outage/battery backup events',
                     action='store_true'
                    )
  group.add_argument(
                     '-r', 
                     '--backup_time_remaining', 
                     help='prints estimated hours of battery backup left',
                     action='store_true'
                    )
  group.add_argument(
                     '-t', 
                     '--site_tariff', 
                     help='lists the utility provider\'s rate plan (tariff) selected for your site in the mobile app '
                          'along with published rates, TOU schedules, etc.',
                     action='store_true'
                    )
  group.add_argument(
                     '-y', 
                     '--site_history', 
                     help='prints summary level information about energy imports and exports down to the day',
                     action='store_true'
                    )
  group.add_argument(
                     '-u', 
                     '--site_tou_history', 
                     help='prints summary level information about energy imports and exports down to the day, separated '
                          'by time of use (peak, partial peak, and off peak)',
                     action='store_true'
                    )
  group.add_argument(
                     '-c', 
                     '--battery_charge_history', 
                     help='prints battery charge level history in 15 minute increments shown on the mobile app',
                     action='store_true'
                    )
  group.add_argument(
                     '-p', 
                     '--power_history', 
                     help='prints energy information in 5 minute increments',
                     action='store_true'
                    )
  group.add_argument(
                     '-f', 
                     '--savings_forecast', 
                     help='prints data for Solar Value (estimated cost savings)',
                     action='store_true'
                    )
  parser.add_argument(
                      '-d', 
                      '--date', 
                      help='DATE of data lookup in m/d/yyyy format',
                      type=lambda d: datetime.strptime(d, '%m/%d/%Y'),
                      nargs=1,
                      metavar='DATE'
                     )

  main(parser)