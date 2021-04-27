import configparser
import os
import GoogleAPI

from Crypto import decrypt
from datetime import datetime
from io import StringIO

buffer = StringIO(
  decrypt(
    os.path.dirname(os.path.abspath(__file__))
    + '/config.rsa'
  ).decode('utf-8')
)
config = configparser.ConfigParser()
config.sections()
config.readfp(buffer)
LOG_SPREADSHEET_ID = config['google']['log_spreadsheet_id']
buffer.close()


##
# Logs errors from try/catch blocks into a Google Sheet.
#
# author: mjhwa@yahoo.com
##
def logError(msg):
  try:
    # write this into an open row in logging Google Sheet
    open_row = GoogleAPI.findOpenRow(LOG_SPREADSHEET_ID, 'error', 'A:A')
  
    inputs = []
    inputs.append({
      'range': 'error!A' + str(open_row),
      'values': [[datetime.today().strftime('%-I:%M:%S %p, %-m/%-d/%Y')]]
    })

    inputs.append({
      'range': 'error!B' + str(open_row),
      'values': [[msg]]
    })

    # batch write data and formula copies to sheet
    service = GoogleAPI.getGoogleSheetService()
    service.spreadsheets().values().batchUpdate(
      spreadsheetId=LOG_SPREADSHEET_ID, 
      body={'data': inputs, 'valueInputOption': 'USER_ENTERED'}
    ).execute()
    service.close()
  except Exception as e:
    print('logError(): ' + str(e))


