import requests
import json
import datetime
import configparser
import os
import zoneinfo
import base64

from Crypto import decrypt, encrypt
from datetime import datetime, timedelta
from io import StringIO

buffer = StringIO(
  decrypt(
    os.path.join(
      os.path.dirname(os.path.abspath(__file__)),
      'token.xor'
    ),
    os.path.join(
      os.path.dirname(os.path.abspath(__file__)),
      'token_key'
    )
  )
)
config = configparser.ConfigParser()
config.sections()
config.read_file(buffer)
REFRESH_TOKEN = config['tesla']['refresh_token']
buffer.close()

PAC = zoneinfo.ZoneInfo('America/Los_Angeles')

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
    'token_key'
  )
)

# Write encoded key for Google Apps Script
s_bytes = (response)['access_token'].encode('ascii')
base64_bytes = base64.b64encode(s_bytes)
base64_string = base64_bytes.decode('ascii')

f = open('/mnt/gdrive/google-apps-script/token.ini', 'wb')
f.write(str.encode(base64_string))
f.close()
