import time
import configparser
import os

from Influxdb import getDBClient
from TeslaEnergyAPI import getSiteStatus, getSiteHistory, getSiteTOUHistory, getBatteryPowerHistory, getSavingsForecast
from GoogleAPI import getGoogleSheetService, findOpenRow
from SendEmail import sendEmail
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
SUMMARY_SHEET_ID = config['google']['summary_sheet_id']
EMAIL_1 = config['notification']['email_1']
buffer.close()


##
# Contains functions to read/write the solar and powerwall data into a 
# InfluxDB for tracking, analysis, and graphs.  The data is a summary level 
# down to the day.
#
# author: mjhwa@yahoo.com
##
def writeSiteTelemetrySummary(date):
  try:
    # get battery data
    data = getSiteStatus()  
    
    json_body = []
    # write battery data
    json_body.append({
      'measurement': 'energy_summary',
      'tags': {
        'source': 'total_pack_energy'
      },
      'time': date.strftime('%Y-%m-%dT%H:%M:%S-7:00'),
      'fields': {
        'value': float(data['response']['total_pack_energy'])
      }
    })

    json_body.append({
      'measurement': 'energy_summary',
      'tags': {
        'source': 'percentage_charged'
      },
      'time': date.strftime('%Y-%m-%dT%H:%M:%S-7:00'),
      'fields': {
        'value': float(data['response']['percentage_charged'])
      }
    })

    # get solar data
    data = getSiteHistory('day', date)

    # write solar data
    for key_1, value_1 in data['response'].items():
      if (isinstance(value_1, list) == True):
        for i in range(len(data['response'][key_1])):
          d = datetime.strptime(
            data['response'][key_1][i]['timestamp'].split('T',1)[0], 
            '%Y-%m-%d'
          )
          if (d.year == date.year
              and d.month == date.month
              and d.day == date.day):
            for key_2, value_2 in data['response'][key_1][i].items():
              if (
                (key_2 != 'timestamp')
                and (key_2 != 'grid_services_energy_exported')
                and (key_2 != 'grid_services_energy_imported')
                and (key_2 != 'generator_energy_exported')
              ):
                json_body.append({
                  'measurement': 'energy_summary',
                  'tags': {
                    'source': key_2
                  },
                  'time': data['response'][key_1][i]['timestamp'],
                  'fields': {
                    'value': float(value_2)
                  }
                })

    # get solar value; need to adjust an additional -1 days because of the lag 
    # in availability of this data
    date = date - timedelta(1)
    data = getSavingsForecast('day', date)

    for i in range(len(data['response'])):
      d = datetime.strptime(
        data['response'][i]['timestamp'].split('T',1)[0],
        '%Y-%m-%d'
      )
      if (d.year == date.year
          and d.month == date.month
          and d.day == date.day):

        json_body.append({
          'measurement': 'energy_summary',
          'tags': {
            'source': 'savings_forecast'
          },
          'time': datetime.strftime(d, '%Y-%m-%dT%H:%M:%S-7:00'),
          'fields': {
            'value': float(data['response'][i]['value'])
          }
        })

    # Write to Influxdb
    client = getDBClient()
    client.switch_database('energy')
    client.write_points(json_body)
    client.close()
  except Exception as e:
    logError('writeSiteTelemetrySummary(): ' + str(e))


##
# Contains functions to read/write the solar and powerwall data, separated 
# by peak/partial peak/off peak, into a Google Sheet for tracking, analysis, 
# and graphs.  The data is a summary level down to the day.
#
# author: mjhwa@yahoo.com
##
def writeSiteTelemetryTOUSummary(date):
  try:
    # get battery data
    data = getSiteStatus()

    inputs = []
    # write total pack energy value
    open_row = findOpenRow(ENERGY_SPREADSHEET_ID, 'Telemetry-Summary','A:A')
    inputs.append({
      'range': 'Telemetry-Summary!A' + str(open_row),
      'values': [[(datetime.today() - timedelta(1)).strftime('%B %d, %Y')]]
    })

    inputs.append({
      'range': 'Telemetry-Summary!B' + str(open_row),
      'values': [[data['response']['total_pack_energy']]]
    })

    inputs.append({
      'range': 'Telemetry-Summary!C' + str(open_row),
      'values': [[data['response']['percentage_charged']]]
    })

    # get solar data for all day
    data = getSiteHistory('day', date)

    # write solar data for all day
    open_row = findOpenRow(ENERGY_SPREADSHEET_ID, 'Telemetry-Summary','F:F')
    for key_1, value_1 in data['response'].items():
      if (isinstance(value_1, list) == True):
        for i in range(len(data['response'][key_1])):
          d = datetime.strptime(
            data['response'][key_1][i]['timestamp'].split('T',1)[0],
            '%Y-%m-%d'
          )

          if (d.year == date.year
              and d.month == date.month
              and d.day == date.day):

            inputs.append({
              'range': 'Telemetry-Summary!F' + str(open_row),
              'values': [[datetime.strftime(d, '%B %d, %Y')]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!H' + str(open_row),
              'values': [[data['response'][key_1][i]['consumer_energy_imported_from_solar']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!I' + str(open_row),
              'values': [[data['response'][key_1][i]['consumer_energy_imported_from_battery']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!J' + str(open_row),
              'values': [[data['response'][key_1][i]['consumer_energy_imported_from_grid']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!K' + str(open_row),
              'values': [[data['response'][key_1][i]['consumer_energy_imported_from_generator']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!L' + str(open_row),
              'values': [[data['response'][key_1][i]['solar_energy_exported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!M' + str(open_row),
              'values': [[data['response'][key_1][i]['battery_energy_exported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!N' + str(open_row),
              'values': [[data['response'][key_1][i]['battery_energy_imported_from_solar']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!O' + str(open_row),
              'values': [[data['response'][key_1][i]['battery_energy_imported_from_grid']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!P' + str(open_row),
              'values': [[data['response'][key_1][i]['battery_energy_imported_from_generator']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!Q' + str(open_row),
              'values': [[data['response'][key_1][i]['grid_energy_imported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!R' + str(open_row),
              'values': [[data['response'][key_1][i]['grid_energy_exported_from_solar']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!S' + str(open_row),
              'values': [[data['response'][key_1][i]['grid_energy_exported_from_battery']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!T' + str(open_row),
              'values': [[data['response'][key_1][i]['grid_energy_exported_from_generator']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!U' + str(open_row),
              'values': [[data['response'][key_1][i]['grid_services_energy_exported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!V' + str(open_row),
              'values': [[data['response'][key_1][i]['grid_services_energy_imported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!W' + str(open_row),
              'values': [[data['response'][key_1][i]['generator_energy_exported']]]
            })

    # copy formulas down
    requests = []
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

    # get solar data for TOU; time needs adjustment for UTC
    data = getSiteTOUHistory('day', (date + timedelta(1)))

    # write solar data for off peak
    open_row = findOpenRow(ENERGY_SPREADSHEET_ID, 'Telemetry-Summary','AE:AE')
    for key_1, value_1 in data['response'].iteritems():
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
              'range': 'Telemetry-Summary!AE' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_solar']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!AF' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_battery']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!AG' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_grid']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!AH' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_generator']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!AI' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['solar_energy_exported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!AJ' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['battery_energy_exported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!AK' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_solar']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!AL' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_grid']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!AM' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_generator']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!AN' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['grid_energy_imported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!AO' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_solar']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!AP' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_battery']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!AQ' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_generator']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!AR' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['grid_services_energy_exported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!AS' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['grid_services_energy_imported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!AT' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['generator_energy_exported']]]
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
              'range': 'Telemetry-Summary!BB' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_solar']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!BC' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_battery']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!BD' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_grid']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!BE' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_generator']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!BF' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['solar_energy_exported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!BG' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['battery_energy_exported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!BH' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_solar']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!BI' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_grid']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!BJ' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_generator']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!BK' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['grid_energy_imported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!BL' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_solar']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!BM' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_battery']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!BN' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_generator']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!BO' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['grid_services_energy_exported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!BP' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['grid_services_energy_imported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!BQ' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['generator_energy_exported']]]
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
              'range': 'Telemetry-Summary!BY' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_solar']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!BZ' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_battery']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!CA' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_grid']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!CB' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['consumer_energy_imported_from_generator']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!CC' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['solar_energy_exported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!CD' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['battery_energy_exported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!CE' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_solar']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!CF' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_grid']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!CG' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['battery_energy_imported_from_generator']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!CH' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['grid_energy_imported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!CI' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_solar']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!CJ' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_battery']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!CK' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['grid_energy_exported_from_generator']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!CL' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['grid_services_energy_exported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!CM' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['grid_services_energy_imported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!CN' + str(open_row),
              'values': [[data['response'][key_1]['time_series'][i]['generator_energy_exported']]]
            })

    # copy formulas down
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
    requests.append({
      'copyPaste': {
        'source': {
          'sheetId': SUMMARY_SHEET_ID,
          'startRowIndex': 4,
          'endRowIndex': 5,
          'startColumnIndex': 99,
          'endColumnIndex': 116
        },
        'destination': {
          'sheetId': SUMMARY_SHEET_ID,
          'startRowIndex': open_row - 1,
          'endRowIndex': open_row,
          'startColumnIndex': 99,
          'endColumnIndex': 116
        },
        'pasteType': 'PASTE_NORMAL'
      }
    })

    # batch write data to sheet
    service = getGoogleSheetService()
    service.spreadsheets().values().batchUpdate(
      spreadsheetId=ENERGY_SPREADSHEET_ID,
      body={'data': inputs, 'valueInputOption': 'USER_ENTERED'}
    ).execute()
    service.spreadsheets().batchUpdate(
      spreadsheetId=ENERGY_SPREADSHEET_ID,
      body={'requests': requests}
    ).execute()
    service.close()
  except Exception as e:
    logError('writeSiteTelemetryTOUSummary(): ' + str(e))


##
# This writes solar and battery data in 5 minute increments in InfluxDB
# for a given day that can be visualized in Grafana.  This recreates the 
# "Energy Usage" graph from the mobile app.  
#
# author: mjhwa@yahoo.com
##
def writeSiteTelemetryDetail(date):
  try:
    # get time series data
    data = getBatteryPowerHistory()

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
    client = getDBClient()
    client.switch_database('energy')
    client.write_points(json_body)
    client.close()
  except Exception as e:
    logError('writeSiteTelemetryDetail(): ' + str(e))


##
# Write the data for the previous day based on a cron job that runs just after
# midnight to ensure we get a full day's worth of data.
#
# author: mjhwa@yahoo.com
##
def main():
  writeSiteTelemetrySummary(datetime.today() - timedelta(1))
  writeSiteTelemetryTOUSummary(datetime.today() - timedelta(1))
  writeSiteTelemetryDetail(datetime.today() - timedelta(1))

  # send email notification
  message = ('Energy telemetry successfully logged on '
             + datetime.today().strftime('%B %d, %Y %H:%M:%S')
             + '.')
  sendEmail(EMAIL_1, 'Energy Telemetry Logged', message, '', '')

if __name__ == "__main__":
  main()

