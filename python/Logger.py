import GoogleAPI

from Utilities import getConfig
from datetime import datetime

LOG_SPREADSHEET_ID = getConfig()['google']['log_spreadsheet_id']


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
    print(datetime.today().strftime('%Y-%m-%d %H:%M:%S') + ' logError(): ' + str(e))


