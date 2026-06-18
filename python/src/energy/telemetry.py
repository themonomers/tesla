import pytz
import argparse

from energy.api import (
  get_site_status, 
  get_site_history, 
  get_site_tou_history, 
  get_power_history, 
  get_savings_forecast, 
  get_battery_charge_history, 
  get_battery_backup_history)
from energy.localtelemetry import get_local_system_status
from common.googleutil import get_google_sheet_service, find_open_row
from common.emailutil import send_email
from common.influxdb import get_db_client
from common.argutil import CustomHelpFormatter
from common.logutil import log
from common.configutil import encrypted_config
from common import constants
from datetime import datetime, timedelta

ENERGY_SPREADSHEET_ID = encrypted_config['google']['energy_spreadsheet_id']
SUMMARY_SHEET_ID = encrypted_config['google']['summary_sheet_id']


##
# This writes solar and battery data in 5 minute increments in InfluxDB
# for a given day that can be visualized in Grafana.  This recreates the 
# "Energy Usage" graph from the mobile app.  
#
# author: mjhwa@yahoo.com
##
def write_energy_detail_to_db(date):
  try:
    # get time series data
    data = get_power_history('day', date)

    json_body = []
    for x in data['response']['time_series']:
      d = datetime.strptime(
        x['timestamp'].split('T',1)[0],
        '%Y-%m-%d'
      )

      if (
        d.year == date.year
        and d.month == date.month
        and d.day == date.day
      ):
        for key, value in x.items():
          if (key != 'timestamp'):
            json_body.append({
              'measurement': 'energy_detail',
              'tags': {
                'source': key
              },
              'time': x['timestamp'],
              'fields': {
                'value': float(value)
              }
            })
        json_body.append({
          'measurement': 'energy_detail',
          'tags': {
            'source': 'load_power'
          },
          'time': x['timestamp'],
          'fields': {
            'value': float(
              x['grid_power']
              + x['battery_power']
              + x['solar_power']
            )
          }
        })

    # Write to Influxdb
    client = get_db_client()
    client.switch_database('energy')
    client.write_points(json_body)
    client.close()
  except Exception as e:
    log().error('write_energy_detail_to_db(): ' + str(e))


##
# Contains functions to read/write the solar and powerwall data into a 
# InfluxDB for tracking, analysis, and graphs.  The data is a summary level 
# down to the day.
#
# author: mjhwa@yahoo.com
##
def write_energy_summary_to_db(date):
  try:
    # get local battery data
    data = get_local_system_status()  
    
    json_body = []
    # write battery data
    json_body.append({
      'measurement': 'energy_summary',
      'tags': {
        'source': 'total_pack_energy'
      },
      'time': str(datetime(
        date.year, 
        date.month, 
        date.day, 
        date.hour, 
        date.minute, 
        date.second,
        date.microsecond
      ).replace(tzinfo=constants.PAC)),
      'fields': {
        'value': float(data['nominal_full_pack_energy'])
      }
    })

    # get battery data
    data = get_site_status()  

    json_body.append({
      'measurement': 'energy_summary',
      'tags': {
        'source': 'percentage_charged'
      },
      'time': str(datetime(
        date.year, 
        date.month, 
        date.day, 
        date.hour, 
        date.minute, 
        date.second,
        date.microsecond
      ).replace(tzinfo=constants.PAC)),
      'fields': {
        'value': float(data['response']['percentage_charged'])
      }
    })

    # get solar data
    data = get_site_history('day', date)

    # write solar data
    cumulative_data = {}

    for items in data['response']['time_series']:
      d = datetime.strptime(
        items['timestamp'].split('T',1)[0], 
        '%Y-%m-%d'
      )

      if (d.year == date.year
          and d.month == date.month
          and d.day == date.day):
        for key, value in items.items():
          if (
            (key != 'timestamp')
            and (key != 'raw_timestamp')
            and (key != 'grid_services_energy_exported')
            and (key != 'grid_services_energy_imported')
            and (key != 'generator_energy_exported')
          ):
            cumulative_data[key] = float(cumulative_data.get(key, 0)) + float(value)
    
    for key, value in cumulative_data.items():
      json_body.append({
        'measurement': 'energy_summary',
        'tags': {
          'source': key
        },
        'time': str(datetime(
          date.year, 
          date.month, 
          date.day, 
          0, 
          0, 
          0, 
          0
        ).replace(tzinfo=constants.PAC)),
        'fields': {
          'value': float(value)
        }
      })

    # get solar value 
    data = get_savings_forecast('day', date)

    for i in range(len(data['response'])):
      d = datetime.strptime(
        data['response'][i]['timestamp'].split('T',1)[0], 
        '%Y-%m-%d'
      )
      local = pytz.timezone('UTC')
      d = local.localize(d, is_dst=None)

      # timestamp in data is in UTC, convert to local time
      d_local = d.astimezone(pytz.timezone(constants.TIME_ZONE))

      # need to adjust an additional -1 days because of the lag in 
      # availability of this data
      if (d_local.year == (date - timedelta(1)).year
          and d_local.month == (date - timedelta(1)).month
          and d_local.day == (date - timedelta(1)).day):

        json_body.append({
          'measurement': 'energy_summary',
          'tags': {
            'source': 'savings_forecast'
          },
          'time': data['response'][i]['timestamp'],
          'fields': {
            'value': float(data['response'][i]['value'])
          }
        })

    # Write to Influxdb
    client = get_db_client()
    client.switch_database('energy')
    client.write_points(json_body)
    client.close()
  except Exception as e:
    log().error('write_energy_summary_to_db(): ' + str(e))


##
# Writes Tesla battery charge state history into an InfluxDB for 
# Grafana visualization.  These are in 15 minute increments.
#
# author: mjhwa@yahoo.com
##
def write_battery_charge_to_db(date):
  try:
    # get battery charge history data
    data = get_battery_charge_history('day', date)

    json_body = []
    dt = ''
    soe = ''
    for x in data['response']['time_series']:
      for key, value in x.items():
        if key == 'timestamp':
          dt = value
        elif key == 'soe':
          soe = value

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
    client = get_db_client()
    client.switch_database('energy')
    client.write_points(json_body)
    client.close()
  except Exception as e:
    log().error('write_battery_charge_to_db(): ' + str(e))


##
# Contains functions to read/write the solar and powerwall data, separated 
# by peak/partial peak/off peak, into InfluxDB for tracking, analysis, 
# and graphs.  The data is a summary level down to the day.
#
# author: mjhwa@yahoo.com
##
def write_energy_tou_summary_to_db(date):
  try:
    json_body = []

    # get solar data for all day
    data = get_site_history('day', date)

    # write solar data for all day
    cumulative_data = {}

    for items in data['response']['time_series']:
      d = datetime.strptime(
        items['timestamp'].split('T',1)[0], 
        '%Y-%m-%d'
      )

      if (d.year == date.year
          and d.month == date.month
          and d.day == date.day):
        for key, value in items.items():
          if (key != 'timestamp') and (key != 'raw_timestamp'):
            cumulative_data[key] = float(cumulative_data.get(key, 0)) + float(value)

    for key, value in cumulative_data.items():
      json_body.append({
        'measurement': 'all_day',
        'tags': {
          'source': key
        },
        'time': str(datetime(
          date.year, 
          date.month, 
          date.day, 
          0, 
          0, 
          0, 
          0
        ).replace(tzinfo=constants.PAC)),
        'fields': {
          'value': float(value)
        }
      })

    # get solar data for TOU
    data = get_site_tou_history('day', date)

    # write solar data for TOU
    for key_1, value_1 in data['response'].items():
      if (key_1 == 'off_peak'
          or key_1 == 'partial_peak'
          or key_1 == 'peak'):
        for i in range(len(data['response'][key_1]['time_series'])):
          d = datetime.strptime(
            data['response'][key_1]['time_series'][i]['timestamp'].split('T',1)[0],
            '%Y-%m-%d'
          )

          if (d.year == date.year
              and d.month == date.month
              and d.day == date.day):
            for key_2, value_2 in data['response'][key_1]['time_series'][i].items():
              if ((key_2 != 'timestamp') and (key_2 != 'raw_timestamp')):
                json_body.append({
                  'measurement': key_1,
                  'tags': {
                    'source': key_2
                  },
                  'time': str(datetime(
                    date.year, 
                    date.month, 
                    date.day, 
                    0, 
                    0, 
                    0, 
                    0
                  ).replace(tzinfo=constants.PAC)),
                  'fields': {
                    'value': float(value_2)
                  }
                })

    # Write to Influxdb
    client = get_db_client()
    client.switch_database('summary')
    client.write_points(json_body)
    client.close()
  except Exception as e:
    log().error('write_energy_tou_summary_to_db(): ' + str(e))


##
# Contains functions to read/write the solar and powerwall data, separated 
# by peak/partial peak/off peak, into a Google Sheet for tracking, analysis, 
# and graphs.  The data is a summary level down to the day.
#
# author: mjhwa@yahoo.com
##
def write_energy_data_to_gsheet(date):
  try:
    # get local battery data
    data = get_local_system_status()

    inputs = []
    # write total pack energy value
    open_row = find_open_row(ENERGY_SPREADSHEET_ID, 'Telemetry!A:A')
    inputs.append({
      'range': 'Telemetry!A' + str(open_row),
      'values': [[(datetime.today() - timedelta(1)).strftime('%B %d, %Y')]]
    })

    inputs.append({
      'range': 'Telemetry!B' + str(open_row),
      'values': [[data['nominal_full_pack_energy']]]
    })

    # get battery data
    data = get_site_status()

    inputs.append({
      'range': 'Telemetry!C' + str(open_row),
      'values': [[data['response']['percentage_charged']]]
    })

    # copy formula down: column D
    requests = []
    requests.append({
      'copyPaste': {
        'source': {
          'sheetId': SUMMARY_SHEET_ID,
          'startRowIndex': 4,
          'endRowIndex': 5,
          'startColumnIndex': 3,
          'endColumnIndex': 4
        },
        'destination': {
          'sheetId': SUMMARY_SHEET_ID,
          'startRowIndex': open_row - 1,
          'endRowIndex': open_row,
          'startColumnIndex': 3,
          'endColumnIndex': 4
        },
        'pasteType': 'PASTE_NORMAL'
      }
    })

    # get solar data for all day
    data = get_site_history('day', date)

    # write solar data for all day
    cumulative_data = {}

    for items in data['response']['time_series']:
      d = datetime.strptime(
        items['timestamp'].split('T',1)[0], 
        '%Y-%m-%d'
      )

      if (d.year == date.year
          and d.month == date.month
          and d.day == date.day):
        for key, value in items.items():
          if (key != 'timestamp') and (key != 'raw_timestamp'):
            cumulative_data[key] = float(cumulative_data.get(key, 0)) + float(value)

    inputs.append({
      'range': 'Telemetry!F' + str(open_row),
      'values': [[datetime.strftime(d, '%B %d, %Y')]]
    })

    inputs.append({
      'range': 'Telemetry!H' + str(open_row),
      'values': [[cumulative_data.get('consumer_energy_imported_from_solar', 0)]]
    })

    inputs.append({
      'range': 'Telemetry!I' + str(open_row),
      'values': [[cumulative_data.get('consumer_energy_imported_from_battery', 0)]]
    })

    inputs.append({
      'range': 'Telemetry!J' + str(open_row),
      'values': [[cumulative_data.get('consumer_energy_imported_from_grid', 0)]]
    })

    inputs.append({
      'range': 'Telemetry!K' + str(open_row),
      'values': [[cumulative_data.get('consumer_energy_imported_from_generator', 0)]]
    })

    inputs.append({
      'range': 'Telemetry!L' + str(open_row),
      'values': [[cumulative_data.get('solar_energy_exported', 0)]]
    })

    inputs.append({
      'range': 'Telemetry!M' + str(open_row),
      'values': [[cumulative_data.get('battery_energy_exported', 0)]]
    })

    inputs.append({
      'range': 'Telemetry!N' + str(open_row),
      'values': [[cumulative_data.get('battery_energy_imported_from_solar', 0)]]
    })

    inputs.append({
      'range': 'Telemetry!O' + str(open_row),
      'values': [[cumulative_data.get('battery_energy_imported_from_grid', 0)]]
    })

    inputs.append({
      'range': 'Telemetry!P' + str(open_row),
      'values': [[cumulative_data.get('battery_energy_imported_from_generator', 0)]]
    })

    inputs.append({
      'range': 'Telemetry!Q' + str(open_row),
      'values': [[cumulative_data.get('grid_energy_imported', 0)]]
    })

    inputs.append({
      'range': 'Telemetry!R' + str(open_row),
      'values': [[cumulative_data.get('grid_energy_exported_from_solar', 0)]]
    })

    inputs.append({
      'range': 'Telemetry!S' + str(open_row),
      'values': [[cumulative_data.get('grid_energy_exported_from_battery', 0)]]
    })

    inputs.append({
      'range': 'Telemetry!T' + str(open_row),
      'values': [[cumulative_data.get('grid_energy_exported_from_generator', 0)]]
    })

    inputs.append({
      'range': 'Telemetry!U' + str(open_row),
      'values': [[cumulative_data.get('grid_services_energy_exported', 0)]]
    })

    inputs.append({
      'range': 'Telemetry!V' + str(open_row),
      'values': [[cumulative_data.get('grid_services_energy_imported', 0)]]
    })

    inputs.append({
      'range': 'Telemetry!W' + str(open_row),
      'values': [[cumulative_data.get('generator_energy_exported', 0)]]
    })

    # copy formulas down: column X to AC
    requests.append({
      'copyPaste': {
        'source': {
          'sheetId': SUMMARY_SHEET_ID,
          'startRowIndex': 4,
          'endRowIndex': 5,
          'startColumnIndex': 23,
          'endColumnIndex': 29
        },
        'destination': {
          'sheetId': SUMMARY_SHEET_ID,
          'startRowIndex': open_row - 1,
          'endRowIndex': open_row,
          'startColumnIndex': 23,
          'endColumnIndex': 29
        },
        'pasteType': 'PASTE_NORMAL'
      }
    })

    # get solar data for TOU
    data = get_site_tou_history('day', date)

    # skip if system set to self-powered
    if (data['response'] != ''):

      # write solar data for off peak
      for key_1, value_1 in data['response'].items():
        if (key_1 == 'off_peak'):
          for i in range(len(data['response'][key_1]['time_series'])):
            d = datetime.strptime(
              data['response'][key_1]['time_series'][i]['timestamp'].split('T',1)[0],
              '%Y-%m-%d'
            )

            if (d.year == date.year
                and d.month == date.month
                and d.day == date.day):

              inputs.append({
                'range': 'Telemetry!AE' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_solar']]]
              })

              inputs.append({
                'range': 'Telemetry!AF' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_battery']]]
              })

              inputs.append({
                'range': 'Telemetry!AG' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_grid']]]
              })

              inputs.append({
                'range': 'Telemetry!AH' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_generator']]]
              })

              inputs.append({
                'range': 'Telemetry!AI' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['solar_energy_exported']]]
              })

              inputs.append({
                'range': 'Telemetry!AJ' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['battery_energy_exported']]]
              })

              inputs.append({
                'range': 'Telemetry!AK' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_solar']]]
              })

              inputs.append({
                'range': 'Telemetry!AL' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_grid']]]
              })

              inputs.append({
                'range': 'Telemetry!AM' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_generator']]]
              })

              inputs.append({
                'range': 'Telemetry!AN' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['grid_energy_imported']]]
              })

              inputs.append({
                'range': 'Telemetry!AO' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_solar']]]
              })

              inputs.append({
                'range': 'Telemetry!AP' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_battery']]]
              })

              inputs.append({
                'range': 'Telemetry!AQ' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_generator']]]
              })

              inputs.append({
                'range': 'Telemetry!AR' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['grid_services_energy_exported']]]
              })

              inputs.append({
                'range': 'Telemetry!AS' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['grid_services_energy_imported']]]
              })

              inputs.append({
                'range': 'Telemetry!AT' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['generator_energy_exported']]]
              })

              # copy formulas down: column AU to AZ
              requests.append({
                'copyPaste': {
                  'source': {
                    'sheetId': SUMMARY_SHEET_ID,
                    'startRowIndex': 4,
                    'endRowIndex': 5,
                    'startColumnIndex': 46,
                    'endColumnIndex': 52
                  },
                  'destination': {
                    'sheetId': SUMMARY_SHEET_ID,
                    'startRowIndex': open_row - 1,
                    'endRowIndex': open_row,
                    'startColumnIndex': 46,
                    'endColumnIndex': 52
                  },
                  'pasteType': 'PASTE_NORMAL'
                }
              })
        elif (key_1 == 'partial_peak'):
          for i in range(len(data['response'][key_1]['time_series'])):
            d = datetime.strptime(
              data['response'][key_1]['time_series'][i]['timestamp'].split('T',1)[0],
              '%Y-%m-%d'
            )

            if (d.year == date.year
                and d.month == date.month
                and d.day == date.day):

              inputs.append({
                'range': 'Telemetry!BB' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_solar']]]
              })

              inputs.append({
                'range': 'Telemetry!BC' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_battery']]]
              })

              inputs.append({
                'range': 'Telemetry!BD' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_grid']]]
              })

              inputs.append({
                'range': 'Telemetry!BE' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_generator']]]
              })

              inputs.append({
                'range': 'Telemetry!BF' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['solar_energy_exported']]]
              })

              inputs.append({
                'range': 'Telemetry!BG' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['battery_energy_exported']]]
              })

              inputs.append({
                'range': 'Telemetry!BH' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_solar']]]
              })

              inputs.append({
                'range': 'Telemetry!BI' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_grid']]]
              })

              inputs.append({
                'range': 'Telemetry!BJ' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_generator']]]
              })

              inputs.append({
                'range': 'Telemetry!BK' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['grid_energy_imported']]]
              })

              inputs.append({
                'range': 'Telemetry!BL' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_solar']]]
              })

              inputs.append({
                'range': 'Telemetry!BM' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_battery']]]
              })

              inputs.append({
                'range': 'Telemetry!BN' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_generator']]]
              })

              inputs.append({
                'range': 'Telemetry!BO' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['grid_services_energy_exported']]]
              })

              inputs.append({
                'range': 'Telemetry!BP' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['grid_services_energy_imported']]]
              })

              inputs.append({
                'range': 'Telemetry!BQ' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['generator_energy_exported']]]
              })

              # copy formulas down: column BR to BW
              requests.append({
                'copyPaste': {
                  'source': {
                    'sheetId': SUMMARY_SHEET_ID,
                    'startRowIndex': 4,
                    'endRowIndex': 5,
                    'startColumnIndex': 69,
                    'endColumnIndex': 75
                  },
                  'destination': {
                    'sheetId': SUMMARY_SHEET_ID,
                    'startRowIndex': open_row - 1,
                    'endRowIndex': open_row,
                    'startColumnIndex': 69,
                    'endColumnIndex': 75
                  },
                  'pasteType': 'PASTE_NORMAL'
                }
              })
        elif (key_1 == 'peak'):
          for i in range(len(data['response'][key_1]['time_series'])):
            d = datetime.strptime(
              data['response'][key_1]['time_series'][i]['timestamp'].split('T',1)[0],
              '%Y-%m-%d'
            )
      
            if (d.year == date.year
                and d.month == date.month
                and d.day == date.day):

              inputs.append({
                'range': 'Telemetry!BY' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_solar']]]
              })

              inputs.append({
                'range': 'Telemetry!BZ' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_battery']]]
              })

              inputs.append({
                'range': 'Telemetry!CA' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_grid']]]
              })

              inputs.append({
                'range': 'Telemetry!CB' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_generator']]]
              })

              inputs.append({
                'range': 'Telemetry!CC' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['solar_energy_exported']]]
              })

              inputs.append({
                'range': 'Telemetry!CD' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['battery_energy_exported']]]
              })

              inputs.append({
                'range': 'Telemetry!CE' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_solar']]]
              })

              inputs.append({
                'range': 'Telemetry!CF' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_grid']]]
              })

              inputs.append({
                'range': 'Telemetry!CG' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_generator']]]
              })

              inputs.append({
                'range': 'Telemetry!CH' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['grid_energy_imported']]]
              })

              inputs.append({
                'range': 'Telemetry!CI' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_solar']]]
              })

              inputs.append({
                'range': 'Telemetry!CJ' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_battery']]]
              })

              inputs.append({
                'range': 'Telemetry!CK' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_generator']]]
              })

              inputs.append({
                'range': 'Telemetry!CL' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['grid_services_energy_exported']]]
              })

              inputs.append({
                'range': 'Telemetry!CM' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['grid_services_energy_imported']]]
              })

              inputs.append({
                'range': 'Telemetry!CN' + str(open_row),
                'values': [[data['response'][key_1]['time_series'][i]['generator_energy_exported']]]
              })

              # copy formulas down: column CO to CT
              requests.append({
                'copyPaste': {
                  'source': {
                    'sheetId': SUMMARY_SHEET_ID,
                    'startRowIndex': 4,
                    'endRowIndex': 5,
                    'startColumnIndex': 92,
                    'endColumnIndex': 98
                  },
                  'destination': {
                    'sheetId': SUMMARY_SHEET_ID,
                    'startRowIndex': open_row - 1,
                    'endRowIndex': open_row,
                    'startColumnIndex': 92,
                    'endColumnIndex': 98
                  },
                  'pasteType': 'PASTE_NORMAL'
                }
              })

      # copy formulas down: column CV to DK 
      requests.append({
        'copyPaste': {
          'source': {
            'sheetId': SUMMARY_SHEET_ID,
            'startRowIndex': 4,
            'endRowIndex': 5,
            'startColumnIndex': 99,
            'endColumnIndex': 115
          },
          'destination': {
            'sheetId': SUMMARY_SHEET_ID,
            'startRowIndex': open_row - 1,
            'endRowIndex': open_row,
            'startColumnIndex': 99,
            'endColumnIndex': 115
          },
          'pasteType': 'PASTE_NORMAL'
        }
      })

    # copy formulas down: column DM to DP, copy from previous row to allow for
    # changes in formula due to electricity rate changes
    requests.append({
      'copyPaste': {
        'source': {
          'sheetId': SUMMARY_SHEET_ID,
          'startRowIndex': open_row - 2,
          'endRowIndex': open_row - 1,
          'startColumnIndex': 116,
          'endColumnIndex': 121
        },
        'destination': {
          'sheetId': SUMMARY_SHEET_ID,
          'startRowIndex': open_row - 1,
          'endRowIndex': open_row,
          'startColumnIndex': 116,
          'endColumnIndex': 121
        },
        'pasteType': 'PASTE_NORMAL'
      }
    })

    # batch write data to sheet
    service = get_google_sheet_service()
    service.spreadsheets().values().batchUpdate(
      spreadsheetId=ENERGY_SPREADSHEET_ID,
      body={'data': inputs, 'valueInputOption': 'USER_ENTERED'}
    ).execute()

    # batch write formula copies
    service.spreadsheets().batchUpdate(
      spreadsheetId=ENERGY_SPREADSHEET_ID,
      body={'requests': requests}
    ).execute()
    service.close()
  except Exception as e:
    log().error('write_energy_data_to_gsheet(): ' + str(e))


##
# Compares the list of backup events already stored in the DB vs. the list
# from the Tesla and inserts any missing events.
#
# author: mjhwa@yahoo.com
##
def write_battery_backup_history_to_db():
  try:
    # get battery backup history data
    data = get_battery_backup_history()

    json_body = []
    local = pytz.timezone(constants.TIME_ZONE)

    # get existing list of backup events saved to DB
    client = get_db_client()
    client.switch_database('outage')
    db = client.query(query='SELECT * FROM "backup"')

    for i in range(len(data['response']['events'])):
      duration = -1
      start = ''
      skip = False

      for key, value in data['response']['events'][i].items():
        if (key == 'duration'):
          duration = float(value) / 1000 / 60 / 60

        if (key == 'timestamp'):
          start = value[0:len(value) - 6:1]
          start = local.localize(
                  datetime.strptime(start, '%Y-%m-%dT%H:%M:%S')
                  , is_dst=None)

        for item in db:
          for j in range(len(item)):
            dt = datetime.strptime(item[j]['time'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.utc)
            dt = dt.astimezone(pytz.timezone('US/Pacific'))

            if start == dt:
              skip = True  # event already in DB, skip

        if ((duration != -1) and (start != '')) and skip != True:
          json_body.append({
            'measurement': 'backup',
            'tags': {
              'source': 'event'
            },
            'time': str(start),
            'fields': {
              'value': float(duration)
            }
          })

    # Write to Influxdb
    client.write_points(json_body)
    client.close()
  except Exception as e:
    log().error('write_battery_backup_history_to_db(): ' + str(e))


##
# Write the data for the previous day based on a cron job that runs just after
# midnight to ensure we get a full day's worth of data.  Also supports manually run 
# data collection for automated routines that failed.
#
# author: mjhwa@yahoo.com
##
def main(parser):
  args = parser.parse_args()

  if not any(vars(args).values()):
    parser.print_help()
    return

  options = [args.detail_to_db, 
             args.summary_to_db, 
             args.tou_summary_to_db, 
             args.data_to_gsheet, 
             args.battery_charge_to_db,
             args.outage_to_db]
  if args.all and any(options):
    parser.error('-a, --all cannot be used with any other options')

  if ((args.detail_to_db or 
       args.summary_to_db or 
       args.tou_summary_to_db or
       args.data_to_gsheet or
       args.battery_charge_to_db) and 
       not args.date):
    parser.error('--date (m/d/yyyy) is required when --detail_to_db, --summary_to_db, --tou_summary_to_db, '
                 '--data_to_gsheet, or --battery_charge_to_db is used')

  if (args.all):
    write_energy_detail_to_db(datetime.today() - timedelta(1))
    write_energy_summary_to_db(datetime.today() - timedelta(1))
    write_battery_charge_to_db(datetime.today() - timedelta(1))
    write_energy_tou_summary_to_db(datetime.today() - timedelta(1))
    write_energy_data_to_gsheet(datetime.today() - timedelta(1))
    write_battery_backup_history_to_db()

    # send email notification
    message = ('Energy telemetry successfully logged on '
              + datetime.today().strftime('%B %d, %Y %H:%M:%S')
              + '.')
    send_email('Energy Telemetry Logged', message, constants.EMAIL_1, '', '', '')
  else:
    date = None
    if (args.date):
      date = datetime.strptime(args.date[0].strftime('%m/%d/%Y'), '%m/%d/%Y') 

    if (args.detail_to_db):
      write_energy_detail_to_db(date)
    
    if (args.summary_to_db):
      write_energy_summary_to_db(date)

    if (args.tou_summary_to_db):
      write_energy_tou_summary_to_db(date)

    if (args.data_to_gsheet):
      write_energy_data_to_gsheet(date)

    if (args.battery_charge_to_db):
      write_battery_charge_to_db(date)

    if (args.outage_to_db):
      write_battery_backup_history_to_db()


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
                    prog='telemetry.py',
                    description='Writes energy data to store for analysis and visualization.',
                    formatter_class=CustomHelpFormatter)
  parser.add_argument(
                      '-a', 
                      '--all', 
                      help='writes all energy data from previous day as part of an automated routine',
                      action='store_true'
                     )
  parser.add_argument(
                      '-e', 
                      '--detail_to_db', 
                      help='writes energy data to InfluxDB in 5 minute increments for Home, Solar, Powerall, and Grid',
                      action='store_true'
                     )
  parser.add_argument(
                      '-s', 
                      '--summary_to_db', 
                      help='writes energy data to InfluxDB of daily totals for Home, Solar, Powerall, and Grid',
                      action='store_true'
                     )
  parser.add_argument(
                      '-t', 
                      '--tou_summary_to_db', 
                      help='writes energy data to InfluxDB of TOU (off peak, partial peak, and peak) breakdowns of '
                           'Solar, Powerall, Grid, etc., Energy Value, and Solar Offset',
                      action='store_true'
                     )
  parser.add_argument(
                      '-g', 
                      '--data_to_gsheet', 
                      help='writes energy data to Google Sheet of TOU (off peak, partial peak, and peak) breakdowns of '
                           'Solar, Powerall, Grid, etc., Energy Value, and Solar Offset',
                      action='store_true'
                     )
  parser.add_argument(
                      '-b', 
                      '--battery_charge_to_db', 
                      help='writes battery charge state history to InfluxDB in 15 minute increments',
                      action='store_true'
                     )
  parser.add_argument(
                      '-o', 
                      '--outage_to_db', 
                      help='writes system backup history/grid outages to InfluxDB',
                      action='store_true'
                     )
  parser.add_argument(
                      '-d', 
                      '--date', 
                      help='DATE of data import in m/d/yyyy format',
                      type=lambda d: datetime.strptime(d, '%m/%d/%Y'),
                      nargs=1,
                      metavar='DATE'
                     )

  main(parser)