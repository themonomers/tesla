import getopt, sys
import common.googleutil as googleutil

from common.utilities import getConfig
from datetime import datetime, timedelta

config = getConfig()
LOG_SPREADSHEET_ID = config['google']['log_spreadsheet_id']
LOG_SHEET_ID = config['google']['log_sheet_id']

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
    open_row = googleutil.findOpenRow(LOG_SPREADSHEET_ID, 'log', 'A:A')
  
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
    service = googleutil.getGoogleSheetService()
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


##
# Keeps the log from getting too long/big; deletes any rows older than
# 30 days.
#
# author: mjhwa@yahoo.com
##
def truncateLog():
  try:
    # get time stamps from each log entry
    service = googleutil.getGoogleSheetService()
    values = service.spreadsheets().values().get(
      spreadsheetId=LOG_SPREADSHEET_ID,
      range='log!B2:B'
    ).execute().get('values', [])
    #print('values: ' + str(values))

    if (not values): return

    # get the date 30 days prior
    thirty_days = datetime.today() - timedelta(30)
    #print('today: ' + str(datetime.today().strftime('%Y-%m-%d %H:%M:%S')))
    #print('30 days: ' + str(thirty_days))

    # loop backwards through each log entry time stamp
    for index, item in reversed(list(enumerate(values))):
      # convert time stamp to Date object
      #print('item: ' + str(item[0]))
      log_date = datetime.strptime(str(item[0]), '%Y-%m-%d %H:%M:%S')
      #print('log date: ' + str(log_date))

      # if the log item is older than 30 days, delete the row and any before it
      # and stop execution
      requests = []
      if (log_date < thirty_days):
        #print('delete rows: ' + 'log!A2:C' + str(index + 2))
        requests.append({
          'deleteDimension': {
            'range': {
              'sheetId': LOG_SHEET_ID,
              'dimension': 'ROWS',
              'startIndex': 1,
              'endIndex': (index + 2)
            }
          }
        })

        # add same number of rows deleted so it doesn't run out of rows
        requests.append({
          'insertDimension': {
            'range': {
              'sheetId': LOG_SHEET_ID,
              'dimension': 'ROWS',
              'startIndex': (len(values) + 1),
              'endIndex': (len(values) + 1 + index + 1)
            }
          }
        })

        service.spreadsheets().batchUpdate(
          spreadsheetId=LOG_SPREADSHEET_ID,
          body={'requests': requests}
        ).execute()

        return
  except Exception as e:
    logError('truncateLog():', e)
  finally:
    service.close()


def printHelp():
  print('Usage: python logger.py [OPTION...]')
  print('')
  print('--help                 prints the usage and options')
  print('--truncate             deletes log entries older than a configured threshold')


def main():
  args = sys.argv[1:]
  options = ''
  long_options = ['help', 'truncate']

  try:
    arguments, values = getopt.getopt(args, options, long_options)

    if len(arguments) < 1: printHelp()

    for currentArg, currentVal in arguments:
      if currentArg in ('--help'):
        printHelp()
      elif currentArg in ('--truncate'):
        truncateLog()
  except getopt.error as e:
    printHelp()


if __name__ == "__main__":
  main()