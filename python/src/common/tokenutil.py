import datetime
import zoneinfo
import requests
import json
import configparser
import argparse

from common.configutil import get_config
from common.logutil import log
from common.argutil import CustomHelpFormatter
from common.crypto import encrypt, decrypt
from common.fileutil import get_filepath
from datetime import datetime, timedelta
from io import StringIO

config = get_config()
CLIENT_ID = config['tesla']['client_id']
TIME_ZONE = config['general']['timezone']
PAC = zoneinfo.ZoneInfo(TIME_ZONE)


##
# Retrievies dictionary of access token values.
#
# author: mjhwa@yahoo.com
##
def get_token():
  buffer = StringIO(
    decrypt(get_filepath('secrets', 'token'), get_filepath('secrets', 'teslaKey'))
  )
  config = configparser.ConfigParser()
  config.sections()
  config.read_file(buffer)
  values = {s:dict(config.items(s)) for s in config.sections()}
  buffer.close()
  
  return values

token = get_token()
REFRESH_TOKEN = token['tesla']['refresh_token']
EXPIRES_AT = token['tesla']['expires_at']


##
# Get new access and refresh tokens and saves it to an encrypted file.
#
# author: mjhwa@yahoo.com 
##
def refresh_token():
  url = 'https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token'

  payload = {
  'grant_type': 'refresh_token',
  'client_id': CLIENT_ID,
  'refresh_token': REFRESH_TOKEN
  }

  response = json.loads(requests.post(url, json=payload).text)

  dt = datetime.now().replace(tzinfo=PAC)

  # Format output
  message =  '[tesla]\n'
  message += 'access_token=' + (response)['access_token'] + '\n'
  message += 'id_token=' + (response)['id_token'] + '\n'
  message += 'refresh_token=' + (response)['refresh_token'] + '\n'
  message += 'created_at=' + datetime.strftime(dt, '%Y-%m-%d %H:%M:%S') + '\n'
  message += 'expires_at=' + datetime.strftime(dt + timedelta(seconds=(response)['expires_in']), '%Y-%m-%d %H:%M:%S') + '\n'
  log().debug('refreshed tokens: ' + message)

  # Encrypt config file
  encrypt(
    message,
    get_filepath('secrets', 'token'),
    get_filepath('secrets', 'teslaKey')
  )


##
# This checks to see if the access token is about to expire and will get
# a new access token from the refresh token.
#
# author:  mjhwa@yahoo.com
##
def check_token_expiration():
  try:
    # get token expiration date
    expiration_date = datetime.strptime(EXPIRES_AT, '%Y-%m-%d %H:%M:%S')

    # get the refresh date 1 hours and 5 minutes prior
    # the additional 5 minutes is because of crontab timing
    refresh_date = expiration_date - timedelta(hours=1, minutes=5)
    log().debug('refresh date: ' + str(refresh_date))
    log().debug('now: ' + str(datetime.today()))

    if (datetime.today() >= refresh_date):
      refresh_token()
  except Exception as e:
    log().error('check_token_expiration(): ' + str(e))


def main(parser):
  args = parser.parse_args()

  if (args.refresh):
    refresh_token()
  elif (args.check):
    check_token_expiration()
  else:
    parser.print_help()


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
                    prog='tokenutil.py',
                    description='Use the refresh token to generate a new access token and refresh token, '
                                'check expiration and refresh if needed.',
                    formatter_class=CustomHelpFormatter)
  group = parser.add_mutually_exclusive_group()
  group.add_argument(
                     '-r', 
                     '--refresh', 
                     help='gets new tokens using the refresh token and saves them to an encrypted file',
                     action='store_true'
                    )
  group.add_argument(
                     '-c', 
                     '--check', 
                     help='checks to see if tokens are expiring and refreshes them and saves them to an encrypted file',
                     action='store_true'
                    )

  main(parser)