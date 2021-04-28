import time
import configparser
import os

from TeslaEnergyAPI import getSiteStatus, getSiteHistory, getBatteryPowerHistory
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
EMAIL_1 = config['notification']['email_1']
buffer.close()


##
# Contains functions to read/write the solar and powerwall data into a 
# Google Sheet for tracking, analysis, and graphs.  The data is a summary
# level down to the day.
#
# author: mjhwa@yahoo.com
##
def writeSiteTelemetrySummary():
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

    # get solar data
    data = getSiteHistory('day')

    # write solar data
    open_row = findOpenRow(ENERGY_SPREADSHEET_ID, 'Telemetry-Summary','F:F')
    for key_1, value_1 in data['response'].items():
      if (isinstance(value_1, list) == True):
        for i in range(len(data['response'][key_1])):
          d = datetime.strptime(
            data['response'][key_1][i]['timestamp'].split('T',1)[0], 
            '%Y-%m-%d'
          )

          if (d.year == (datetime.today() - timedelta(1)).year
              and d.month == (datetime.today() - timedelta(1)).month
              and d.day == (datetime.today() - timedelta(1)).day):
            inputs.append({
              'range': 'Telemetry-Summary!F' + str(open_row),
              'values': [[d.strftime('%B %d, %Y')]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!G' + str(open_row),
              'values': [[data['response'][key_1][i]['consumer_energy_imported_from_solar']]]
            })
   
            inputs.append({
              'range': 'Telemetry-Summary!H' + str(open_row),
              'values': [[data['response'][key_1][i]['battery_energy_imported_from_generator']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!I' + str(open_row),
              'values': [[data['response'][key_1][i]['grid_energy_exported_from_battery']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!J' + str(open_row),
              'values': [[data['response'][key_1][i]['consumer_energy_imported_from_generator']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!K' + str(open_row),
              'values': [[data['response'][key_1][i]['grid_energy_imported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!L' + str(open_row),
              'values': [[data['response'][key_1][i]['grid_energy_exported_from_solar']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!M' + str(open_row),
              'values': [[data['response'][key_1][i]['battery_energy_imported_from_solar']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!N' + str(open_row),
              'values': [[data['response'][key_1][i]['grid_services_energy_exported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!O' + str(open_row),
              'values': [[data['response'][key_1][i]['grid_energy_exported_from_generator']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!P' + str(open_row),
              'values': [[data['response'][key_1][i]['battery_energy_exported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!Q' + str(open_row),
              'values': [[data['response'][key_1][i]['consumer_energy_imported_from_grid']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!R' + str(open_row),
              'values': [[data['response'][key_1][i]['grid_services_energy_imported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!S' + str(open_row),
              'values': [[data['response'][key_1][i]['solar_energy_exported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!T' + str(open_row),
              'values': [[data['response'][key_1][i]['generator_energy_exported']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!U' + str(open_row),
              'values': [[data['response'][key_1][i]['consumer_energy_imported_from_battery']]]
            })

            inputs.append({
              'range': 'Telemetry-Summary!V' + str(open_row),
              'values': [[data['response'][key_1][i]['battery_energy_imported_from_grid']]]
            })

    # batch write data to sheet
    service = getGoogleSheetService()
    service.spreadsheets().values().batchUpdate(
      spreadsheetId=ENERGY_SPREADSHEET_ID, 
      body={'data': inputs, 'valueInputOption': 'USER_ENTERED'}
    ).execute()
    service.close()
  except Exception as e:
    logError('writeSiteTelemetrySummary(): ' + str(e))


##
# This writes solar and battery data in 5 minute increments for a given day
# that recreates the "Energy Usage" graph in the mobile app.  
#
# This needs to be refactored into a Telagraf database, instead of Google
# Sheet, for scalability and visualization, as well as other benefits with  
# Grafana.
#
# author: mjhwa@yahoo.com
##
def writeSiteTelemetryDetail(date):
  try:
    # get time series data
    data = getBatteryPowerHistory()

    inputs = []
    open_row = findOpenRow(ENERGY_SPREADSHEET_ID, 'Telemetry-Detail','A:A')
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
        d = datetime.strptime(
          x['timestamp'].split('T',1)[0]
          + ' '
          + x['timestamp'].split('T',1)[1].split('-',1)[0], 
          '%Y-%m-%d %H:%M:%S'
        )

        inputs.append({
          'range': 'Telemetry-Detail!A' + str(open_row),
          'values': [[str(d)]]
        })

        inputs.append({
          'range': 'Telemetry-Detail!B' + str(open_row),
          'values': [[x['grid_power']]]
        })

        inputs.append({
          'range': 'Telemetry-Detail!C' + str(open_row),
          'values': [[x['battery_power']]]
        })

        inputs.append({
          'range': 'Telemetry-Detail!D' + str(open_row),
          'values': [[x['generator_power']]]
        })

        inputs.append({
          'range': 'Telemetry-Detail!E' + str(open_row),
          'values': [[x['solar_power']]]
        })

        inputs.append({
          'range': 'Telemetry-Detail!F' + str(open_row),
          'values': [[x['grid_services_power']]]
        })
        open_row += 1

    # batch write data to sheet
    service = getGoogleSheetService()
    service.spreadsheets().values().batchUpdate(
      spreadsheetId=ENERGY_SPREADSHEET_ID,
      body={'data': inputs, 'valueInputOption': 'USER_ENTERED'}
    ).execute()
    service.close()
  except Exception as e:
    logError('writeSiteTelemetryDetail(): ' + str(e))


##
# 
#
# author: mjhwa@yahoo.com
##
def main():
  writeSiteTelemetrySummary()
  writeSiteTelemetryDetail(datetime.today() - timedelta(1))

  # send email notification
  message = ('Energy telemetry successfully logged on '
             + datetime.today().strftime('%B %d, %Y %H:%M:%S')
             + '.')
  sendEmail(EMAIL_1, 'Energy Telemetry Logged', message, '')

if __name__ == "__main__":
  main()

