import datetime
import requests
import json
import argparse
import urllib
import zoneinfo

from common.crypto import encrypt
from common.argutil import CustomHelpFormatter
from common.logutil import log
from common.configutil import (
  encrypted_config, 
  config, 
  get_filepath, 
  get_config)
from datetime import datetime, timedelta

CLIENT_ID = encrypted_config['tesla']['client_id']
CLIENT_SECRET = encrypted_config['tesla']['client_secret']
BASE_AUTH_URL = config['uri']['tesla_base_auth_url']
BASE_FLEET_URL = config['uri']['tesla_base_fleet_url']
USER_AUTH_URL = config['uri']['tesla_user_auth_url']
REDIRECT_URI = config['uri']['tesladeveloper_redirect_uri']
SCOPE = 'openid offline_access vehicle_device_data vehicle_location vehicle_cmds vehicle_charging_cmds vehicle_specs energy_device_data energy_cmds'
PAC = zoneinfo.ZoneInfo(config['general']['timezone'])


##
# Retrievies dictionary of access token values.
#
# author: mjhwa@yahoo.com
##
def get_token():
  return get_config(get_filepath('token'), get_filepath('tesla_key'))

token = get_token()
REFRESH_TOKEN = token['tesla']['refresh_token']
EXPIRES_AT = token['tesla']['expires_at']


##
# Get new access and refresh tokens using the refresh token and 
# saves it to an encrypted file.
#
# author: mjhwa@yahoo.com 
##
def refresh_token():
  payload = {
  'grant_type': 'refresh_token',
  'client_id': CLIENT_ID,
  'refresh_token': REFRESH_TOKEN
  }

  response = json.loads(requests.post(BASE_AUTH_URL, json=payload).text)

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
    get_filepath('token'),
    get_filepath('tesla_key')
  )


##
# Checks to see if the access token is about to expire and will get
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


##
# Gets new access and refresh token using web login credentials and saves 
# them to a file.  Acquired tokens are stored in current working directory 
# in tesla_token.ini file for persistence by default.
#
# author: mjhwa@yahoo.com 
##
def new_token():
  print('Please go to this URL: \n')
  url = (USER_AUTH_URL
        + '&client_id=' + urllib.parse.quote(CLIENT_ID, safe='')
        + '&redirect_uri=' + urllib.parse.quote(REDIRECT_URI, safe='')
        + '&scope=' + urllib.parse.quote(SCOPE, safe=''))

  print(url)
  print('\nAfter successful Tesla account authorization, you will be redirected to the specified redirect_uri.')
  code = input('\nPlease extract and paste the code URL parameter from this callback: ')

  if not code:
    print('\nNo code provided, exiting code exchange.')
    return
  else:
    print('\nExecuting code exchange to generate tokens...')

  payload = {
      "grant_type": "authorization_code",
      "client_id": CLIENT_ID,
      "client_secret": CLIENT_SECRET,
      "code": code,
      "audience": BASE_FLEET_URL,
      "redirect_uri": REDIRECT_URI,
      "scope:": SCOPE
  }

  response = json.loads(requests.post(BASE_AUTH_URL, json=payload).text)

  dt = datetime.now().replace(tzinfo=PAC)

  message =  '[tesla]\n'
  message += 'access_token=' + (response)['access_token'] + '\n'
  message += 'id_token=' + (response)['id_token'] + '\n'
  message += 'refresh_token=' + (response)['refresh_token'] + '\n'
  message += 'created_at=' + datetime.strftime(dt, '%Y-%m-%d %H:%M:%S') + '\n'
  message += 'expires_at=' + datetime.strftime(dt + timedelta(seconds=(response)['expires_in']), '%Y-%m-%d %H:%M:%S') + '\n'
  log().debug('tokens: ' + message)

  f = open('tesla_token.ini', 'wb')
  f.write(str.encode(message))
  f.close()

  print('\nTokens saved in current working directory in tesla_token.ini.  Never share these tokens with anyone, '
        'as it acts as a digital "valet key" that allows third-party services or malicious actors to track your '
        'car\'s location, control climate settings, and even unlock or drive your vehicle without a physical key.')


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
                    description='Tesla authentication flow to retrieve new access and refresh token '
                                'and check expiration and refresh if needed.',
                    formatter_class=CustomHelpFormatter)
  group = parser.add_mutually_exclusive_group()
  group.add_argument(
                     '-n', 
                     '--new', 
                     help='gets new access and refresh token using web login credentials and saves them to a file',
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