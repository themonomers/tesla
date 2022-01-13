import configparser
import os
import Logger
import TeslaRefreshToken

from Crypto import simpleDecrypt
from datetime import timedelta, datetime
from io import StringIO

buffer = StringIO(
  simpleDecrypt(
    os.path.join(
      os.path.dirname(os.path.abspath(__file__)),
      'token.xor'
    )
  ).decode('utf-8')
)
config = configparser.ConfigParser()
config.sections()
config.readfp(buffer)
EXPIRES_AT = config['tesla']['expires_at']
buffer.close()


##
# This checks to see if the access token is about to expire and will get
# a new access token from the refresh token.
#
# author:  mjhwa@yahoo.com
##
def checkTokenExpiration():
  try:
    # get token expiration date
    expiration_date = datetime.strptime(EXPIRES_AT, '%Y-%m-%d %H:%M:%S')

    # get the refresh date (2 hours prior)
    refresh_date = expiration_date - timedelta(hours=2)
    #print('refresh date: ' + str(refresh_date))
    #print('now: ' + str(datetime.today()))

    if (datetime.today() >= refresh_date):
      TeslaRefreshToken
  except Exception as e:
    Logger.logError('checkTokenExpiration(): ' + str(e))


def main():
  checkTokenExpiration()

if __name__ == "__main__":
  main()
