from GoogleAPI import getGoogleMailService
from Utilities import getConfig
from Logger import logError
from datetime import datetime, timedelta

QUERIES = getConfig()['query']
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

    if ('messages' not in messages):
      return
   
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
    logError('truncateEmail(): ' + str(e))
  finally:
    service.close()


def main():
  for key, value in QUERIES.items():
    truncateEmail(value)


if __name__ == "__main__":
  main()
