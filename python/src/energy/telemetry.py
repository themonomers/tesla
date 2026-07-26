import pytz
import argparse

from energy.api import (
  get_site_status, 
  get_site_history, 
  get_site_tou_history, 
  get_power_history, 
  get_savings_forecast, 
  get_battery_charge_history, 
  get_battery_backup_history
)
from energy.localtelemetry import get_local_system_status
from common.googleutil import get_google_sheet_service, find_open_row
from common.emailutil import send_email
from common.influxdb import get_db_client
from common.argutil import CustomHelpFormatter
from common.logutil import log
from common.configutil import encrypted_config
from common.constants import (
  PAC,
  TIME_ZONE,
  EMAIL_1
)
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
def write_energy_detail_to_db(target_date):
  try:
    # get time series data
    data = get_power_history('day', target_date)

    json_body = []
    for x in data['response']['time_series']:
      d = datetime.strptime(x['timestamp'].split('T',1)[0], '%Y-%m-%d')

      if d.date() == target_date.date():
        for key, value in x.items():
          if key != 'timestamp':
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
            'value': float(x['grid_power'] + x['battery_power'] + x['solar_power'])
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
def write_energy_summary_to_db(target_date):
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
        target_date.year, 
        target_date.month, 
        target_date.day, 
        target_date.hour, 
        target_date.minute, 
        target_date.second,
        target_date.microsecond
      ).replace(tzinfo=PAC)),
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
        target_date.year, 
        target_date.month, 
        target_date.day, 
        target_date.hour, 
        target_date.minute, 
        target_date.second,
        target_date.microsecond
      ).replace(tzinfo=PAC)),
      'fields': {
        'value': float(data['response']['percentage_charged'])
      }
    })

    # get solar data
    data = get_site_history('day', target_date)

    # write solar data
    cumulative_data = {}

    for items in data['response']['time_series']:
      d = datetime.strptime(items['timestamp'].split('T',1)[0], '%Y-%m-%d')

      if d.date() == target_date.date():
        for key, value in items.items():
          if key not in {
            'timestamp',
            'raw_timestamp',
            'grid_services_energy_exported', 
            'grid_services_energy_imported', 
            'generator_energy_exported'
          }:            
            cumulative_data[key] = float(cumulative_data.get(key, 0)) + float(value)
    
    for key, value in cumulative_data.items():
      json_body.append({
        'measurement': 'energy_summary',
        'tags': {
          'source': key
        },
        'time': str(datetime(
          target_date.year, 
          target_date.month, 
          target_date.day, 
          0, 
          0, 
          0, 
          0
        ).replace(tzinfo=PAC)),
        'fields': {
          'value': float(value)
        }
      })

    # get solar value 
    data = get_savings_forecast('day', target_date)

    for i in range(len(data['response'])):
      d = datetime.strptime(data['response'][i]['timestamp'].split('T',1)[0], '%Y-%m-%d')
      local = pytz.timezone('UTC')
      d = local.localize(d, is_dst=None)

      # timestamp in data is in UTC, convert to local time
      d_local = d.astimezone(pytz.timezone(TIME_ZONE))

      # need to adjust an additional -1 days because of the lag in 
      # availability of this data
      if d_local.date() == (target_date - timedelta(1)).date():
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
def write_battery_charge_to_db(target_date):
  try:
    # get battery charge history data
    data = get_battery_charge_history('day', target_date)

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
def write_energy_tou_summary_to_db(target_date):
  try:
    json_body = []

    # get solar data for all day
    data = get_site_history('day', target_date)

    # write solar data for all day
    cumulative_data = {}

    for items in data['response']['time_series']:
      d = datetime.strptime(items['timestamp'].split('T',1)[0], '%Y-%m-%d')

      if d.date() == target_date.date():
        for key, value in items.items():
          if key not in {'timestamp', 'raw_timestamp'}:
            cumulative_data[key] = float(cumulative_data.get(key, 0)) + float(value)

    for key, value in cumulative_data.items():
      json_body.append({
        'measurement': 'all_day',
        'tags': {
          'source': key
        },
        'time': str(datetime(
          target_date.year, 
          target_date.month, 
          target_date.day, 
          0, 
          0, 
          0, 
          0
        ).replace(tzinfo=PAC)),
        'fields': {
          'value': float(value)
        }
      })

    # get solar data for TOU
    data = get_site_tou_history('day', target_date)

    # write solar data for TOU
    for key_1, _ in data['response'].items():
      if key_1 in {'off_peak', 'partial_peak', 'peak'}:
        for i in range(len(data['response'][key_1]['time_series'])):
          d = datetime.strptime(
            data['response'][key_1]['time_series'][i]['timestamp'].split('T',1)[0],
            '%Y-%m-%d'
          )

          if d.date() == target_date.date():
            for key_2, value_2 in data['response'][key_1]['time_series'][i].items():
              if key_2 not in {'timestamp', 'raw_timestamp'}:
                json_body.append({
                  'measurement': key_1,
                  'tags': {
                    'source': key_2
                  },
                  'time': str(datetime(
                    target_date.year, 
                    target_date.month, 
                    target_date.day, 
                    0, 
                    0, 
                    0, 
                    0
                  ).replace(tzinfo=PAC)),
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
def write_energy_data_to_gsheet(target_date):
  try:
    # get local battery data
    data = get_local_system_status()

    inputs = []
    # write total pack energy value
    open_row = find_open_row(ENERGY_SPREADSHEET_ID, 'Telemetry!A:A')
    inputs.append({
      'range': f'Telemetry!A{open_row}',
      'values': [[(datetime.today() - timedelta(1)).strftime('%B %d, %Y')]]
    })

    inputs.append({
      'range': f'Telemetry!B{open_row}',
      'values': [[data['nominal_full_pack_energy']]]
    })

    # get battery data
    data = get_site_status()

    inputs.append({
      'range': f'Telemetry!C{open_row}',
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
    data = get_site_history('day', target_date)

    # write solar data for all day
    cumulative_data = {}

    for items in data['response']['time_series']:
      d = datetime.strptime(items['timestamp'].split('T',1)[0], '%Y-%m-%d')

      if d.date() == target_date.date():
        for key, value in items.items():
          if key not in {'timestamp', 'raw_timestamp'}:
            cumulative_data[key] = float(cumulative_data.get(key, 0)) + float(value)

    inputs.append({
      'range': f'Telemetry!F{open_row}',
      'values': [[datetime.strftime(d, '%B %d, %Y')]]
    })

    inputs.append({
      'range': f'Telemetry!H{open_row}',
      'values': [[cumulative_data.get('consumer_energy_imported_from_solar', 0)]]
    })

    inputs.append({
      'range': f'Telemetry!I{open_row}',
      'values': [[cumulative_data.get('consumer_energy_imported_from_battery', 0)]]
    })

    inputs.append({
      'range': f'Telemetry!J{open_row}',
      'values': [[cumulative_data.get('consumer_energy_imported_from_grid', 0)]]
    })

    inputs.append({
      'range': f'Telemetry!K{open_row}',
      'values': [[cumulative_data.get('consumer_energy_imported_from_generator', 0)]]
    })

    inputs.append({
      'range': f'Telemetry!L{open_row}',
      'values': [[cumulative_data.get('solar_energy_exported', 0)]]
    })

    inputs.append({
      'range': f'Telemetry!M{open_row}',
      'values': [[cumulative_data.get('battery_energy_exported', 0)]]
    })

    inputs.append({
      'range': f'Telemetry!N{open_row}',
      'values': [[cumulative_data.get('battery_energy_imported_from_solar', 0)]]
    })

    inputs.append({
      'range': f'Telemetry!O{open_row}',
      'values': [[cumulative_data.get('battery_energy_imported_from_grid', 0)]]
    })

    inputs.append({
      'range': f'Telemetry!P{open_row}',
      'values': [[cumulative_data.get('battery_energy_imported_from_generator', 0)]]
    })

    inputs.append({
      'range': f'Telemetry!Q{open_row}',
      'values': [[cumulative_data.get('grid_energy_imported', 0)]]
    })

    inputs.append({
      'range': f'Telemetry!R{open_row}',
      'values': [[cumulative_data.get('grid_energy_exported_from_solar', 0)]]
    })

    inputs.append({
      'range': f'Telemetry!S{open_row}',
      'values': [[cumulative_data.get('grid_energy_exported_from_battery', 0)]]
    })

    inputs.append({
      'range': f'Telemetry!T{open_row}',
      'values': [[cumulative_data.get('grid_energy_exported_from_generator', 0)]]
    })

    inputs.append({
      'range': f'Telemetry!U{open_row}',
      'values': [[cumulative_data.get('grid_services_energy_exported', 0)]]
    })

    inputs.append({
      'range': f'Telemetry!V{open_row}',
      'values': [[cumulative_data.get('grid_services_energy_imported', 0)]]
    })

    inputs.append({
      'range': f'Telemetry!W{open_row}',
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
    data = get_site_tou_history('day', target_date)

    # skip if system set to self-powered
    if data['response']:

      # write solar data for off peak
      for key_1, _ in data['response'].items():
        if key_1 == 'off_peak':
          for i in range(len(data['response'][key_1]['time_series'])):
            d = datetime.strptime(
              data['response'][key_1]['time_series'][i]['timestamp'].split('T',1)[0],
              '%Y-%m-%d'
            )

            if d.date() == target_date.date():
              inputs.append({
                'range': f'Telemetry!AE{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_solar']]]
              })

              inputs.append({
                'range': f'Telemetry!AF{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_battery']]]
              })

              inputs.append({
                'range': f'Telemetry!AG{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_grid']]]
              })

              inputs.append({
                'range': f'Telemetry!AH{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_generator']]]
              })

              inputs.append({
                'range': f'Telemetry!AI{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['solar_energy_exported']]]
              })

              inputs.append({
                'range': f'Telemetry!AJ{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['battery_energy_exported']]]
              })

              inputs.append({
                'range': f'Telemetry!AK{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_solar']]]
              })

              inputs.append({
                'range': f'Telemetry!AL{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_grid']]]
              })

              inputs.append({
                'range': f'Telemetry!AM{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_generator']]]
              })

              inputs.append({
                'range': f'Telemetry!AN{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['grid_energy_imported']]]
              })

              inputs.append({
                'range': f'Telemetry!AO{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_solar']]]
              })

              inputs.append({
                'range': f'Telemetry!AP{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_battery']]]
              })

              inputs.append({
                'range': f'Telemetry!AQ{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_generator']]]
              })

              inputs.append({
                'range': f'Telemetry!AR{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['grid_services_energy_exported']]]
              })

              inputs.append({
                'range': f'Telemetry!AS{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['grid_services_energy_imported']]]
              })

              inputs.append({
                'range': f'Telemetry!AT{open_row}',
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
        elif key_1 == 'partial_peak':
          for i in range(len(data['response'][key_1]['time_series'])):
            d = datetime.strptime(
              data['response'][key_1]['time_series'][i]['timestamp'].split('T',1)[0],
              '%Y-%m-%d'
            )

            if d.date() == target_date.date():
              inputs.append({
                'range': f'Telemetry!BB{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_solar']]]
              })

              inputs.append({
                'range': f'Telemetry!BC{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_battery']]]
              })

              inputs.append({
                'range': f'Telemetry!BD{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_grid']]]
              })

              inputs.append({
                'range': f'Telemetry!BE{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_generator']]]
              })

              inputs.append({
                'range': f'Telemetry!BF{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['solar_energy_exported']]]
              })

              inputs.append({
                'range': f'Telemetry!BG{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['battery_energy_exported']]]
              })

              inputs.append({
                'range': f'Telemetry!BH{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_solar']]]
              })

              inputs.append({
                'range': f'Telemetry!BI{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_grid']]]
              })

              inputs.append({
                'range': f'Telemetry!BJ{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_generator']]]
              })

              inputs.append({
                'range': f'Telemetry!BK{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['grid_energy_imported']]]
              })

              inputs.append({
                'range': f'Telemetry!BL{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_solar']]]
              })

              inputs.append({
                'range': f'Telemetry!BM{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_battery']]]
              })

              inputs.append({
                'range': f'Telemetry!BN{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_generator']]]
              })

              inputs.append({
                'range': f'Telemetry!BO{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['grid_services_energy_exported']]]
              })

              inputs.append({
                'range': f'Telemetry!BP{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['grid_services_energy_imported']]]
              })

              inputs.append({
                'range': f'Telemetry!BQ{open_row}',
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
        elif key_1 == 'peak':
          for i in range(len(data['response'][key_1]['time_series'])):
            d = datetime.strptime(
              data['response'][key_1]['time_series'][i]['timestamp'].split('T',1)[0],
              '%Y-%m-%d'
            )
      
            if d.date() == target_date.date():
              inputs.append({
                'range': f'Telemetry!BY{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_solar']]]
              })

              inputs.append({
                'range': f'Telemetry!BZ{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_battery']]]
              })

              inputs.append({
                'range': f'Telemetry!CA{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_grid']]]
              })

              inputs.append({
                'range': f'Telemetry!CB{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_generator']]]
              })

              inputs.append({
                'range': f'Telemetry!CC{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['solar_energy_exported']]]
              })

              inputs.append({
                'range': f'Telemetry!CD{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['battery_energy_exported']]]
              })

              inputs.append({
                'range': f'Telemetry!CE{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_solar']]]
              })

              inputs.append({
                'range': f'Telemetry!CF{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_grid']]]
              })

              inputs.append({
                'range': f'Telemetry!CG{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_generator']]]
              })

              inputs.append({
                'range': f'Telemetry!CH{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['grid_energy_imported']]]
              })

              inputs.append({
                'range': f'Telemetry!CI{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_solar']]]
              })

              inputs.append({
                'range': f'Telemetry!CJ{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_battery']]]
              })

              inputs.append({
                'range': f'Telemetry!CK{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_generator']]]
              })

              inputs.append({
                'range': f'Telemetry!CL{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['grid_services_energy_exported']]]
              })

              inputs.append({
                'range': f'Telemetry!CM{open_row}',
                'values': [[data['response'][key_1]['time_series'][i]['grid_services_energy_imported']]]
              })

              inputs.append({
                'range': f'Telemetry!CN{open_row}',
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
    local = pytz.timezone(TIME_ZONE)

    # get existing list of backup events saved to DB
    client = get_db_client()
    client.switch_database('outage')
    db = client.query(query='SELECT * FROM "backup"')

    for i in range(len(data['response']['events'])):
      duration = -1
      start = ''
      skip = False

      for key, value in data['response']['events'][i].items():
        if key == 'duration':
          duration = float(value) / 1000 / 60 / 60

        if key == 'timestamp':
          start = value[0:len(value) - 6:1]
          start = local.localize(datetime.strptime(start, '%Y-%m-%dT%H:%M:%S'), is_dst=None)

        for item in db:
          for j in range(len(item)):
            dt = datetime.strptime(item[j]['time'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.utc)
            dt = dt.astimezone(pytz.timezone(TIME_ZONE))

            if start == dt:
              skip = True  # event already in DB, skip

        if duration != -1 and start and not skip:
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

  options = [
    args.detail_to_db, 
    args.summary_to_db, 
    args.tou_summary_to_db, 
    args.data_to_gsheet, 
    args.battery_charge_to_db,
    args.outage_to_db
  ]
  if args.write_all and any(options):
    parser.error('-a, --all cannot be used with any other options')

  if (
      (
        args.detail_to_db 
        or args.summary_to_db
        or args.tou_summary_to_db
        or args.data_to_gsheet
        or args.battery_charge_to_db
      )
      and not args.target_date
  ):
    parser.error(
      '--target_date (m/d/yyyy) is required when --detail_to_db, --summary_to_db, --tou_summary_to_db, '
      '--data_to_gsheet, or --battery_charge_to_db is used'
    )

  if args.write_all:
    write_energy_detail_to_db(datetime.today() - timedelta(1))
    write_energy_summary_to_db(datetime.today() - timedelta(1))
    write_battery_charge_to_db(datetime.today() - timedelta(1))
    write_energy_tou_summary_to_db(datetime.today() - timedelta(1))
    write_energy_data_to_gsheet(datetime.today() - timedelta(1))
    write_battery_backup_history_to_db()

    # send email notification
    message = f'Energy telemetry successfully logged on {datetime.today():%B %d, %Y %H:%M:%S}.'
    send_email('Energy Telemetry Logged', message, EMAIL_1)
  else:
    target_date = None
    if args.target_date:
      target_date = datetime.strptime(args.target_date[0].strftime('%m/%d/%Y'), '%m/%d/%Y') 

    if args.detail_to_db:
      write_energy_detail_to_db(target_date)
    
    if args.summary_to_db:
      write_energy_summary_to_db(target_date)

    if args.tou_summary_to_db:
      write_energy_tou_summary_to_db(target_date)

    if args.data_to_gsheet:
      write_energy_data_to_gsheet(target_date)

    if args.battery_charge_to_db:
      write_battery_charge_to_db(target_date)

    if args.outage_to_db:
      write_battery_backup_history_to_db()


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
    prog='telemetry.py',
    description='Writes energy data to store for analysis and visualization.',
    formatter_class=CustomHelpFormatter
  )
  parser.add_argument(
    '-a', 
    '--write_all', 
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
    '--target_date', 
    help='DATE of data import in m/d/yyyy format',
    type=lambda d: datetime.strptime(d, '%m/%d/%Y'),
    nargs=1,
    metavar='DATE'
  )

  main(parser)