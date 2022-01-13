import requests
import json
import urllib
import datetime
import configparser
import os
import tzlocal

from Crypto import simpleDecrypt
from itertools import cycle, izip
from datetime import datetime, timedelta
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
REFRESH_TOKEN = config['tesla']['refresh_token']
buffer.close()

# Exchange bearer token for access token
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

dt = datetime.now()

# write output to config file
message =  '[tesla]\n'
message += 'access_token=' + (response)['access_token'] + '\n'
message += 'refresh_token=' + (response)['refresh_token'] + '\n'
message += 'created_at=' + datetime.strftime(dt, '%Y-%m-%d %H:%M:%S') + '\n'
message += 'expires_at=' + datetime.strftime(tzlocal.get_localzone().localize(dt + timedelta(seconds=(response)['expires_in'])), '%Y-%m-%d %H:%M:%S') + '\n'

# Read key
key_file = open(
  os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'token_key'
  ), 'rb'
)
key = key_file.read()
key_file.close()

# Encrypt with key
encrypted = ''.join(chr(ord(c)^ord(k)) for c,k in izip(message, cycle(key)))

# Write encrypted file
f = open(
  os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'token.xor'
  ), 'wb'
)
f.write(encrypted)
f.close()
