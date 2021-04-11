import smtplib
import configparser

from Logger import logError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

config = configparser.ConfigParser()
config.sections()
config.read('config.ini')
SENDER_EMAIL = config['notification']['sender_email']
SENDER_PASSWORD = config['notification']['sender_password']

##
# Send email via Google SMTP.
#
# author: mjhwa@yahoo.com
##
def sendEmail(to, subject, message, cc):
  try:
    sender = SENDER_EMAIL
    cc = [cc]
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(SENDER_EMAIL, [to] + cc, msg.as_string()) 
    server.close()
  except Exception as e:
    logError('sendEmail(): ' + str(e))
