import smtplib
import os

from Utilities import getConfig
from Logger import logError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

config = getConfig()
SENDER_EMAIL = config['notification']['sender_email']
SENDER_PASSWORD = config['notification']['sender_password']


##
# Send email via Google SMTP.
#
# author: mjhwa@yahoo.com
##
def sendEmail(to, subject, message, cc, filename):
  try:
    sender = SENDER_EMAIL
    cc = [cc]
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

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
    server.sendmail(SENDER_EMAIL, [to] + cc, msg.as_string()) 
    server.close()
  except Exception as e:
    logError('sendEmail(): ' + str(e))


