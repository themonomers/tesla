import configparser
import Logger

from GoogleAPI import getGoogleMailService
from Crypto import decrypt
from datetime import datetime, timedelta
from io import StringIO

buffer = StringIO(decrypt('/home/pi/tesla/python/config.rsa').decode('utf-8'))
config = configparser.ConfigParser()
config.sections()
config.readfp(buffer)
QUERY_1 = config['notification']['query_1']
QUERY_2 = config['notification']['query_2']
QUERY_3 = config['notification']['query_3']
QUERY_4 = config['notification']['query_4']
buffer.close()

DELETE_THRESHOLD = 30


##
# Keeps the email sent folder from being overloaded with notifications; deletes 
# any notification emails older than a specified number of days.
#
# author: mjhwa@yahoo.com
##
def truncateEmail(query):
  try:
    # get the date for the threshold (days prior)
    delete_date = datetime.today() - timedelta(DELETE_THRESHOLD)
    #print('threshold: ' + str(delete_date))

    # Call the Gmail API and get the messages based on query
    service = getGoogleMailService()
    messages = service.users().messages().list(
                 userId='me',
                 q=query
               ).execute()

    # Loop through all the messages returned
    for item in messages['messages']:
      #print(item['id'])
      message = service.users().messages().get(
                  userId='me',
                  id=item['id']
                ).execute()

      email_date = datetime.fromtimestamp(int(message['internalDate'])/1000)
      #print(email_date)

      # Check if the email date is older than the delete date threshold and
      # move to trash
      if (email_date < delete_date):
        #print(str(email_date) + ' ' + str(message['payload']['headers'][8]))
        message = service.users().messages().trash(
                    userId='me',
                    id=item['id']
                  ).execute() 
  except Exception as e:
    Logger.logError('truncateEmail(): ' + str(e))
  finally:
    service.close()


def main():
  truncateEmail(QUERY_1)
  truncateEmail(QUERY_2)
  truncateEmail(QUERY_3)
  truncateEmail(QUERY_4)

if __name__ == "__main__":
  main()


