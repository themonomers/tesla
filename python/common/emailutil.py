import smtplib
import os
import time
import getopt, sys

from common.googleutil import get_google_mail_service
from common.utilities import get_config
from common.logger import log_error, log_error_retry
from email.mime.image import MIMEImage
from email.message import EmailMessage
from datetime import datetime, timedelta

config = get_config()
SENDER_EMAIL = config['notification']['sender_email']
SENDER_PASSWORD = config['notification']['sender_password']
QUERIES = config['query']

WAIT_TIME = 30
DELETE_THRESHOLD = 30


##
# Send email via Google SMTP.
#
# author: mjhwa@yahoo.com
##
def send_email(subject, body, to, cc, bcc, filename):
  try:
    msg = EmailMessage()
    msg.set_content(body)
    msg['From'] = SENDER_EMAIL
    msg['Subject'] = subject
    msg['To'] = to

    if cc:
      msg['Cc'] = cc
    if bcc:
      msg['Bcc'] = bcc

    if (filename != ''):
      f = file( # type: ignore
        os.path.join(
          os.path.dirname(os.path.abspath(__file__)),
          filename
        ), 'rb'
      )
      msg.attach(
        MIMEImage(
          f.read(),
          name=os.path.basename(filename),
          _subtype='svg+xml'
        )
      )

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.send_message(msg)
    server.close()
  except Exception as e:
    log_error_retry('send_email(): ' + str(e))
    time.sleep(WAIT_TIME)
    send_email(subject, body, to, cc, bcc, filename)


##
# Keeps the email sent folder from being overloaded with notifications; deletes 
# any notification emails older than a specified number of days.
#
# author: mjhwa@yahoo.com
##
def truncate_email(query):
  try:
    # get the date for the threshold (days prior)
    delete_date = datetime.today() - timedelta(DELETE_THRESHOLD)
    #print('threshold: ' + str(delete_date))

    # Call the Gmail API and get the messages based on query
    service = get_google_mail_service()
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
    log_error('truncate_email():', e)
  finally:
    service.close()


def print_help():
  print('Usage: python emailutil.py [OPTION...]')
  print('')
  print('--help                 prints the usage and options')
  print('--truncate             deletes filtered emails older than a configured threshold')


def main():
  args = sys.argv[1:]
  options = ''
  long_options = ['help', 'truncate']

  try:
    arguments, values = getopt.getopt(args, options, long_options)

    if len(arguments) < 1: print_help()

    for currentArg, currentVal in arguments:
      if currentArg in ('--help'):
        print_help()
      elif currentArg in ('--truncate'):
        for key in QUERIES:
          truncate_email(QUERIES[key])
  except getopt.error as e:
    print_help()


if __name__ == "__main__":
  main()