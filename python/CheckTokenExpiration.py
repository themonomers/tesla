import configparser

from GoogleAPI import getGoogleSheetService
from SendEmail import sendEmail
from Logger import logError
from datetime import timedelta, datetime

config = configparser.ConfigParser()
config.sections()
config.read('config.ini')
EV_SPREADSHEET_ID = config['google']['ev_spreadsheet_id']
EMAIL_1 = config['notification']['email_1']


##
# This checks to see if the access token expires in a week or less and will 
# send an email reminder to get a new one.
#
# author:  mjhwa@yahoo.com
##
def main():
  try:
    # get token expiration date
    service = getGoogleSheetService()
    expiration_date = service.spreadsheets().values().get(
      spreadsheetId=EV_SPREADSHEET_ID,
      range='Smart Charger!H5'
    ).execute().get('values', [])[0][0]
    expiration_date = datetime.strptime(expiration_date, '%m/%d/%Y')

    # get the date for the reminder (7 days prior)
    reminder_date = expiration_date - timedelta(7)
    #print('reminder date: ' + str(reminder_date))
    #print('now: ' + str(datetime.today()))

    if (datetime.today() >= reminder_date):
      message = ('Your Tesla Access Token is expiring on ' 
                 + str(expiration_date)
                 + '.  Please generate a new token soon.')
      sendEmail(EMAIL_1, 'Tesla Access Token Expiring Soon', message, '')
  except Exception as e:
    logError('checkTokenExpiration(): ' + str(e))
  finally:
    service.close()

if __name__ == "__main__":
  main()
