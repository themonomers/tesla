import teslapy
import datetime
import zoneinfo
import requests
import json
import os
import argparse

from common.logger import log_error
from common.crypto import encrypt
from common.utilities import get_config, get_token, NewlineFormatter
from datetime import datetime, timedelta

token = get_token()
REFRESH_TOKEN = token['tesla']['refresh_token']
EXPIRES_AT = token['tesla']['expires_at']

TIME_ZONE = get_config()['general']['timezone']
PAC = zoneinfo.ZoneInfo(TIME_ZONE)

##
# Uses https://github.com/tdorssers/TeslaPy. To install, run:  
# python -m pip install teslapy
#
# Acquired tokens are stored in current working directory in 
# cache.json file for persistence by default.
#
# @todo rolling index crypto keys: http://bitly.com/2WXBRNp
#
# author: mjhwa@yahoo.com 
##
def new_token():
  try:
    with teslapy.Tesla('elon@tesla.com') as tesla:
        response = tesla.fetch_token()

    expires_at = datetime.fromtimestamp(response['expires_at'], tz=PAC)

    # print outputs to screen
    print('[tesla]')
    print('access_token=' + response['access_token'])
    print('refresh_token=' + response['refresh_token'])
    print('created_at=' + datetime.strftime(expires_at - timedelta(seconds = response['expires_in']), '%Y-%m-%d %H:%M:%S'))
    print('expires_at=' + datetime.strftime(expires_at, '%Y-%m-%d %H:%M:%S'))
  except Exception as e:
    log_error('new_token():', e)


##
# Get new access and refresh tokens and saves it to an encrypted file.
#
# author: mjhwa@yahoo.com 
##
def refresh_token():
  try:
    url = 'https://auth.tesla.com/oauth2/v3/token'
    payload = {
    'grant_type': 'refresh_token',
    'client_id': 'ownerapi',
    'refresh_token': REFRESH_TOKEN,
    'scope': 'openid email offline_access'
    }

    response = json.loads(requests.post(
                url,
                json=payload
            ).text)

    dt = datetime.now().replace(tzinfo=PAC)

    # Format output
    message =  '[tesla]\n'
    message += 'access_token=' + (response)['access_token'] + '\n'
    message += 'refresh_token=' + (response)['refresh_token'] + '\n'
    message += 'created_at=' + datetime.strftime(dt, '%Y-%m-%d %H:%M:%S') + '\n'
    message += 'expires_at=' + datetime.strftime(dt + timedelta(seconds=(response)['expires_in']), '%Y-%m-%d %H:%M:%S') + '\n'

    # Encrypt config file
    encrypt(
    message,
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'token.xor'
    ),
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'tesla_private_key.pem'
    )
    )
  except Exception as e:
    log_error('refresh_token():', e)


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
    #print('refresh date: ' + str(refresh_date))
    #print('now: ' + str(datetime.today()))

    if (datetime.today() >= refresh_date):
      refresh_token()
  except Exception as e:
    log_error('check_token_expiration():', e)


def main(parser):
  args = parser.parse_args()

  if (args.new):
    new_token()
  elif (args.refresh):
    refresh_token()
  elif (args.check):
    check_token_expiration()
  else:
    parser.print_help()


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
                    prog='tokenutil.py',
                    description='API call for the Tesla authentication flow to retrieve new access and refresh tokens, '
                                'check expiration and refresh if needed.',
                    formatter_class=NewlineFormatter)
  group = parser.add_mutually_exclusive_group()
  group.add_argument(
                     '-n', 
                     '--new', 
                     help='prints a new access and refresh token using web login credentials',
                     action='store_true'
                    )
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