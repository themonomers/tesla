import smtplib
import os

from Utilities import getConfig
from Logger import logError
from email.mime.image import MIMEImage
from email.message import EmailMessage

config = getConfig()
SENDER_EMAIL = config['notification']['sender_email']
SENDER_PASSWORD = config['notification']['sender_password']


##
# Send email via Google SMTP.
#
# author: mjhwa@yahoo.com
##
def sendEmail(subject, body, to, cc, bcc, filename):
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
    logError('sendEmail(): ' + str(e))


