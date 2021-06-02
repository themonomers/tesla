import requests
import json
import urllib
import datetime
import configparser
import os
import GoogleAPI

from Crypto import decrypt
from io import StringIO

buffer = StringIO(
  decrypt(
    os.path.join(
      os.path.dirname(os.path.abspath(__file__)),
      'config.rsa'
    )
  ).decode('utf-8')
)
config = configparser.ConfigParser()
config.sections()
config.readfp(buffer)
EV_SPREADSHEET_ID = config['google']['ev_spreadsheet_id']
buffer.close()


refresh_token = raw_input('refresh token: ')

# Exchange bearer token for access token
url = 'https://owner-api.teslamotors.com/oauth/token'
payload = {
  'grant_type': 'refresh_token',
  'refresh_token': refresh_token,
  'client_id': '81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384',
  'client_secret': 'c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3'
}

response = requests.post(
             url,
             json=payload
           )

print(json.loads(response.text))

# print outputs to screen
print('# access_token=' + json.loads(response.text)['access_token'])
print(
  '# expires_at: '
  + str(
    datetime.datetime.fromtimestamp(
      json.loads(response.text)['created_at']
      + json.loads(response.text)['expires_in']
    )
  )
)
print('# refresh_token: ' + json.loads(response.text)['refresh_token'])
print(
  '# created_at: '
  + str(
    datetime.datetime.fromtimestamp(
      json.loads(response.text)['created_at']
    )
  )
)

# write timestamp into Google Sheet for crontab expiration checks
inputs = [{
  'range': 'Smart Charger!H5',
  'values': [[datetime.datetime.fromtimestamp(
    json.loads(response.text)['created_at']
    + json.loads(response.text)['expires_in']
  ).strftime('%m/%d/%Y')]]
}]
service = GoogleAPI.getGoogleSheetService()
service.spreadsheets().values().batchUpdate(
  spreadsheetId=EV_SPREADSHEET_ID,
  body={'data': inputs, 'valueInputOption': 'USER_ENTERED'}
).execute()
service.close()


