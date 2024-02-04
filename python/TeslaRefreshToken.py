import requests
import json
import datetime
import os
import zoneinfo

from Crypto import encrypt
from Utilities import getConfig, getToken
from datetime import datetime, timedelta

REFRESH_TOKEN = getToken()['tesla']['refresh_token']

TIME_ZONE = getConfig()['general']['timezone']
PAC = zoneinfo.ZoneInfo(TIME_ZONE)

# Get new access and refresh tokens
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