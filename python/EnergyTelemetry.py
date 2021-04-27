import time
import configparser

from TeslaEnergyAPI import getSiteStatus
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
    # get rollup of vehicle data
    data = getSiteStatus()  
    
    inputs = []
    # write date stamp
    open_row = findOpenRow(ENERGY_SPREADSHEET_ID, 'Telemetry','A:A')
    inputs.append({
      'range': 'Telemetry!A' + str(open_row),
      'values': [[datetime.today().strftime('%B %d, %Y')]]
    })

    # write total pack energy value
    inputs.append({
      'range': 'Telemetry!B' + str(open_row),
      'values': [[data['response']['total_pack_energy']]]
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

