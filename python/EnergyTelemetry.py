import time
import configparser

from TeslaEnergyAPI import getSiteStatus, getSiteHistory
from GoogleAPI import getGoogleSheetService, findOpenRow
from SendEmail import sendEmail
from Crypto import decrypt
from Logger import logError
from datetime import datetime
from io import StringIO

buffer = StringIO(decrypt('config.rsa').decode('utf-8'))
config = configparser.ConfigParser()
config.sections()
config.readfp(buffer)
ENERGY_SPREADSHEET_ID = config['google']['energy_spreadsheet_id']
EMAIL_1 = config['notification']['email_1']
buffer.close()


##
# Contains functions to read/write the solar and powerwall data into a 
# Google Sheet for tracking, analysis, and graphs.
#
# author: mjhwa@yahoo.com
##
def writeSiteTelemetry():
  try:
    # get battery data
    data = getSiteStatus()  
    
    inputs = []
    # write total pack energy value
    open_row = findOpenRow(ENERGY_SPREADSHEET_ID, 'Telemetry','A:A')
    inputs.append({
      'range': 'Telemetry!A' + str(open_row),
      'values': [[datetime.today().strftime('%B %d, %Y')]]
    })

    inputs.append({
      'range': 'Telemetry!B' + str(open_row),
      'values': [[data['response']['total_pack_energy']]]
    })

    # get solar data
    data = getSiteHistory('day')

    # write solar data
    open_row = findOpenRow(ENERGY_SPREADSHEET_ID, 'Telemetry','F:F')
    for key_1, value_1 in data['response'].items():
      if (isinstance(value_1, list) == True):
        for i in range(len(data['response'][key_1])):
          d = datetime.strptime(
            data['response'][key_1][i]['timestamp'].split('T',1)[0], 
            '%Y-%m-%d'
          )

          if (d.year == datetime.today().year
              and d.month == datetime.today().month
              and d.day == datetime.today().day):
            inputs.append({
              'range': 'Telemetry!F' + str(open_row),
              'values': [[d.strftime('%B %d, %Y')]]
            })

            inputs.append({
              'range': 'Telemetry!G' + str(open_row),
              'values': [[data['response'][key_1][i]['consumer_energy_imported_from_solar']]]
            })
   
            inputs.append({
              'range': 'Telemetry!H' + str(open_row),
              'values': [[data['response'][key_1][i]['battery_energy_imported_from_generator']]]
            })

            inputs.append({
              'range': 'Telemetry!I' + str(open_row),
              'values': [[data['response'][key_1][i]['grid_energy_exported_from_battery']]]
            })

            inputs.append({
              'range': 'Telemetry!J' + str(open_row),
              'values': [[data['response'][key_1][i]['consumer_energy_imported_from_generator']]]
            })

            inputs.append({
              'range': 'Telemetry!K' + str(open_row),
              'values': [[data['response'][key_1][i]['grid_energy_imported']]]
            })

            inputs.append({
              'range': 'Telemetry!L' + str(open_row),
              'values': [[data['response'][key_1][i]['grid_energy_exported_from_solar']]]
            })

            inputs.append({
              'range': 'Telemetry!M' + str(open_row),
              'values': [[data['response'][key_1][i]['battery_energy_imported_from_solar']]]
            })

            inputs.append({
              'range': 'Telemetry!N' + str(open_row),
              'values': [[data['response'][key_1][i]['grid_services_energy_exported']]]
            })

            inputs.append({
              'range': 'Telemetry!O' + str(open_row),
              'values': [[data['response'][key_1][i]['grid_energy_exported_from_generator']]]
            })

            inputs.append({
              'range': 'Telemetry!P' + str(open_row),
              'values': [[data['response'][key_1][i]['battery_energy_exported']]]
            })

            inputs.append({
              'range': 'Telemetry!Q' + str(open_row),
              'values': [[data['response'][key_1][i]['consumer_energy_imported_from_grid']]]
            })

            inputs.append({
              'range': 'Telemetry!R' + str(open_row),
              'values': [[data['response'][key_1][i]['grid_services_energy_imported']]]
            })

            inputs.append({
              'range': 'Telemetry!S' + str(open_row),
              'values': [[data['response'][key_1][i]['solar_energy_exported']]]
            })

            inputs.append({
              'range': 'Telemetry!T' + str(open_row),
              'values': [[data['response'][key_1][i]['generator_energy_exported']]]
            })

            inputs.append({
              'range': 'Telemetry!U' + str(open_row),
              'values': [[data['response'][key_1][i]['consumer_energy_imported_from_battery']]]
            })

            inputs.append({
              'range': 'Telemetry!V' + str(open_row),
              'values': [[data['response'][key_1][i]['battery_energy_imported_from_grid']]]
            })

    # batch write data to sheet
    service = getGoogleSheetService()
    service.spreadsheets().values().batchUpdate(
      spreadsheetId=ENERGY_SPREADSHEET_ID, 
      body={'data': inputs, 'valueInputOption': 'USER_ENTERED'}
    ).execute()
    service.close()
    
    # send email notification
    message = ('Energy telemetry successfully logged on ' 
               + datetime.today().strftime('%B %d, %Y %H:%M:%S') 
               + '.')
    sendEmail(EMAIL_1, 'Energy Telemetry Logged', message, '')
  except Exception as e:
    logError('writeSiteTelemetry(): ' + str(e))


##
# 
#
# author: mjhwa@yahoo.com
##
def main():
  writeSiteTelemetry()

if __name__ == "__main__":
  main()

