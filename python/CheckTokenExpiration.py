from Logger import logError
from Utilities import getToken
from datetime import timedelta, datetime

config = getToken()
EXPIRES_AT = config['tesla']['expires_at']


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

    # get the refresh date 1 hours and 5 minutes prior
    # the additional 5 minutes is because of crontab timing
    refresh_date = expiration_date - timedelta(hours=1, minutes=5)
    #print('refresh date: ' + str(refresh_date))
    #print('now: ' + str(datetime.today()))

    if (datetime.today() >= refresh_date):
      import TeslaRefreshToken
  except Exception as e:
    logError('checkTokenExpiration(): ' + str(e))


def main():
  checkTokenExpiration()

if __name__ == "__main__":
  main()
