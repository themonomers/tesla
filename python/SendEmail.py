import smtplib

from Logger import *
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

##
# Send email via Google SMTP
#
# author: mjhwa@yahoo.com
##
def sendEmail(to, subject, message, cc):
  try:
    sender = ''
    cc = [cc]
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login(sender, '')
    server.sendmail(sender, [to] + cc, msg.as_string())
    server.close()
  except Exception as e:
    print('sendEmail(): ' + str(e))
    logError('sendEmail(): ' + str(e))
