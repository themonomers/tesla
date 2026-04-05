import GoogleAPI

from Utilities import getConfig
from datetime import datetime

LOG_SPREADSHEET_ID = getConfig()['google']['log_spreadsheet_id']
INFO = 'INFO'
WARN = 'WARN'
ERROR = 'ERROR'

##
# Logs information into a Google Sheet.
#
# author: mjhwa@yahoo.com
##
def log(level, msg):
  try:
    # write this into an open row in logging Google Sheet
    open_row = GoogleAPI.findOpenRow(LOG_SPREADSHEET_ID, 'log', 'A:A')
  
    inputs = []
    inputs.append({
      'range': 'log!A' + str(open_row),
      'values': [[level]]
    })
    inputs.append({
      'range': 'log!B' + str(open_row),
      'values': [[datetime.today().strftime('%Y-%m-%d %H:%M:%S')]]
    })
    inputs.append({
      'range': 'log!C' + str(open_row),
      'values': [[msg]]
    })
    
    # batch write data and formula copies to sheet
    service = GoogleAPI.getGoogleSheetService()
    service.spreadsheets().values().batchUpdate(
      spreadsheetId=LOG_SPREADSHEET_ID, 
      body={'data': inputs, 'valueInputOption': 'USER_ENTERED'}
    ).execute()
    service.close()

    if level == ERROR:
      exit(1)
  except Exception as e:
    logErrorStdOut('log():', e)


##
# Log errors to standard output.
#
# author: mjhwa@yahoo.com
##
def logErrorStdOut(msg, e):
  print('[ERROR] ' + datetime.today().strftime('%Y-%m-%d %H:%M:%S') + ' ' + msg + ' ' + str(e))


def logInfo(msg):
  log(INFO, msg)


def logWarn(msg):
  log(WARN, msg)

 
def logError(msg):
  log(ERROR, msg)