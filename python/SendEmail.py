import smtplib
import configparser

from Crypto import decrypt
from Logger import logError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import StringIO

buffer = StringIO(decrypt('config.rsa').decode('utf-8'))
config = configparser.ConfigParser()
config.sections()
config.readfp(buffer)
SENDER_EMAIL = config['notification']['sender_email']
SENDER_PASSWORD = config['notification']['sender_password']
buffer.close()


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
