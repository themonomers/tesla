import configparser

from Telemetry import findOpenRow
from GoogleAPI import *
from datetime import datetime, timedelta

config = configparser.ConfigParser()
config.sections()
config.read('config.ini')
LOG_SPREADSHEET_ID = config['google']['log_spreadsheet_id']
ERROR_SHEET_ID = config['google']['error_sheet_id']

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
    'values': [[datetime.today().strftime('%-I:%M:%S %p, %-m/%-d/%Y')]]
  })

  inputs.append({
    'range': 'error!B' + str(open_row),
    'values': [[msg]]
  })

  # batch write data and formula copies to sheet
  service = getGoogleSheetService()
  service.spreadsheets().values().batchUpdate(
    spreadsheetId=LOG_SPREADSHEET_ID, 
    body={'data': inputs, 'valueInputOption': 'USER_ENTERED'}
  ).execute()
  service.close()


##
# Keeps the error log from getting too long/big; deletes any rows older than 
# 30 days.  
#
# author: mjhwa@yahoo.com
##
def truncateLog():
  try:
    # get time stamps from each log entry
    service = getGoogleSheetService()
    values = service.spreadsheets().values().get(
      spreadsheetId=LOG_SPREADSHEET_ID,
      range='error!A:A'
    ).execute().get('values', [])
    #print('values: ' + str(values))

    if (not values): return

    # get the date 30 days prior
    thirty_days = datetime.today() - timedelta(30)
    #print('today: ' + str(datetime.today().strftime('%I:%M:%S %p, %m/%d/%Y')))
    print('30 days: ' + str(thirty_days))
  
    # loop backwards through each log entry time stamp 
    for index, item in reversed(list(enumerate(values))):
      # convert time stamp to Date object
      #print('item: ' + str(item[0]))
      log_date = datetime.strptime(str(item[0]), '%I:%M:%S %p, %m/%d/%Y')
      #print('log date: ' + str(log_date))
    
      # if the log item is older than 30 days, delete the row and any before it 
      # and stop execution
      requests = []
      if (log_date < thirty_days):
        #print('delete rows: ' + 'error!A1:B' + str(index + 1))
        requests.append({
          'deleteDimension': {
            'range': {
              'sheetId': ERROR_SHEET_ID,
              'dimension': 'ROWS',
              'startIndex': 0,
              'endIndex': (index + 1)
            }
          }
        })
        service.spreadsheets().batchUpdate(
          spreadsheetId=LOG_SPREADSHEET_ID, 
          body={'requests': requests}
        ).execute()

        return
  except Exception as e:
    logError('truncateLog(): ' + str(e))
  finally:
    service.close()


