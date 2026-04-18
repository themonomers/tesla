import GoogleAPI

from Utilities import getConfig
from datetime import datetime

LOG_SPREADSHEET_ID = getConfig()['google']['log_spreadsheet_id']
INFO = 'INFO'
WARN = 'WARN'
ERROR = 'ERROR'
ERROR_RETRY = 'ERROR_RETRY'

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


def logInfo(msg):
  log(INFO, msg)


def logWarn(msg):
  log(WARN, msg)

 
def logError(msg, error):
  log(ERROR, msg + ' ' + str(error))


def logErrorRetry(msg):
  log(ERROR_RETRY, msg)


##
# Log errors to standard output.
#
# author: mjhwa@yahoo.com
##
def logStdOut(level, msg):
  print('[' + level + '] ' + datetime.today().strftime('%Y-%m-%d %H:%M:%S') + ' ' + msg)

  if level == ERROR:
    exit(1)


def logInfoStdOut(msg):
  logStdOut(INFO, msg)


def logWarnStdOut(msg):
  logStdOut(WARN, msg)


def logErrorStdOut(msg, error):
  logStdOut(ERROR, msg + ' ' + str(error))


def logErrorRetryStdOut(msg):
  logStdOut(ERROR_RETRY, msg)