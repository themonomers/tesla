from Telemetry import findOpenRow
from GoogleAPI import *
from datetime import datetime

LOG_SPREADSHEET_ID = ''

##
# Logs errors from try/catch blocks into a Google Sheet.
#
# author: mjhwa@yahoo.com
##
def logError(msg):
  # write this into an open row in logging Google Sheet
  open_row = findOpenRow(LOG_SPREADSHEET_ID, 'error', 'A:A')

  inputs = []
  inputs.append({
    'range': 'error!A' + str(open_row),
    'values': [[datetime.today().strftime('%H:%M:%S, %m/%d/%Y')]]
  })

  inputs.append({
    'range': 'error!B' + str(open_row),
    'values': [[msg]]
  })

  # batch write data and formula copies to sheet
  service = getGoogleSheetService()
  service.spreadsheets().values().batchUpdate(spreadsheetId=LOG_SPREADSHEET_ID, body={'data': inputs, 'valueInputOption': 'USER_ENTERED'}).execute()
  service.close()
