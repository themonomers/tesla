import argparse
import common.googleutil as googleutil

from common.utilities import get_config, NewlineFormatter
from datetime import datetime, timedelta

config = get_config()
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
    open_row = googleutil.find_open_row(LOG_SPREADSHEET_ID, 'log', 'A:A')
  
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
    service = googleutil.get_google_sheet_service()
    service.spreadsheets().values().batchUpdate(
      spreadsheetId=LOG_SPREADSHEET_ID, 
      body={'data': inputs, 'valueInputOption': 'USER_ENTERED'}
    ).execute()
    service.close()

    if level == ERROR:
      exit(1)
  except Exception as e:
    log_error_std_out('log():', e)


def log_info(msg):
  log(INFO, msg)


def log_warn(msg):
  log(WARN, msg)

 
def log_error(msg, error):
  log(ERROR, msg + ' ' + str(error))


def log_error_retry(msg):
  log(ERROR_RETRY, msg)


##
# Log errors to standard output.
#
# author: mjhwa@yahoo.com
##
def log_std_out(level, msg):
  print('[' + level + '] ' + datetime.today().strftime('%Y-%m-%d %H:%M:%S') + ' ' + msg)

  if level == ERROR:
    exit(1)


def log_info_std_out(msg):
  log_std_out(INFO, msg)


def log_warn_std_out(msg):
  log_std_out(WARN, msg)


def log_error_std_out(msg, error):
  log_std_out(ERROR, msg + ' ' + str(error))


def log_error_retry_std_out(msg):
  log_std_out(ERROR_RETRY, msg)


##
# Keeps the log from getting too long/big; deletes any rows older than
# 30 days.
#
# author: mjhwa@yahoo.com
##
def truncate_log():
  try:
    # get time stamps from each log entry
    service = googleutil.get_google_sheet_service()
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
    log_error('truncate_log():', e)
  finally:
    service.close()


def main(parser):
  args = parser.parse_args()

  if (args.truncate):
    truncate_log()
  else:
    parser.print_help()


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
                    prog='logger.py',
                    description='Central logging service.',
                    formatter_class=NewlineFormatter)
  parser.add_argument(
                      '-t', 
                      '--truncate', 
                      help='deletes log entries older than a configured threshold',
                      action='store_true'
                     )

  main(parser)