import requests
import hashlib
import base64
import urllib
import json
import datetime
import getpass
import configparser
import GoogleAPI

from random import choice
from string import hexdigits
from Crypto import decrypt
from io import StringIO

buffer = StringIO(decrypt('config.rsa').decode('utf-8'))
config = configparser.ConfigParser()
config.sections()
config.readfp(buffer)
EV_SPREADSHEET_ID = config['google']['ev_spreadsheet_id']
buffer.close()


email = raw_input('email: ')
password = getpass.getpass('password: ')
passcode = raw_input('passcode: ')

# Step 1: Obtain the login page
code_verifier = ''.join(choice(hexdigits) for i in range(86))
#print('code: ' + code_verifier)

code_challenge = base64.b64encode(
  hashlib.sha256(
    code_verifier.encode('utf-8')
  ).digest()
)
#print('challenge: ' + code_challenge)

url = ('https://auth.tesla.com/oauth2/v3/authorize'
       + '?client_id=ownerapi'
       + '&code_challenge=' 
       + code_challenge
       + '&code_challenge_method=S256'
       + '&redirect_uri=' 
       + urllib.quote('https://auth.tesla.com/void/callback')
       + '&response_type=code'
       + '&scope=' 
       + urllib.quote('openid email offline_access')
       + '&state=state')
#print('url: ' + url)

response = requests.get(url)
#print(response.content)

csrf = response.content[
         response.content.find('name="_csrf"') + 20: 
         response.content.find('name="_csrf"') + 56
       ]
phase = response.content[
          response.content.find('name="_phase"') + 21: 
          response.content.find('name="_phase"') + 33
        ]
process = response.content[
            response.content.find('name="_process"') + 23: 
            response.content.find('name="_process"') + 24
          ]
transaction_id = response.content[
                   response.content.find('name="transaction_id"') + 29: 
                   response.content.find('name="transaction_id"') + 37
                 ]
cookie = response.headers.get('Set-Cookie')

#print('csrf: ' + csrf)
#print('phase: ' + phase)
#print('process: ' + process)
#print('trasaction_id: ' + transaction_id)
#print('cookie: ' + cookie)

# Step 2: Authenticate user name and password
payload = {
  '_csrf': csrf,
  '_phase': phase,
  '_process': process,
  'transaction_id': transaction_id,
  'cancel': '',
  'identity': email,
  'credential': password
}

response = requests.post(
             url, 
             data=payload, 
             headers={'Cookie': cookie}
           )

# Step 3: Authenticate MFA
url =  ('https://auth.tesla.com/oauth2/v3/authorize/mfa/factors'
        + '?transaction_id=' 
        + transaction_id)

response = requests.get(url, headers={'Cookie': cookie})

url = 'https://auth.tesla.com/oauth2/v3/authorize/mfa/verify'
#print('factor_id: ' + json.loads(response.text)['data'][0]['id'])
payload = {
  'factor_id': json.loads(response.text)['data'][0]['id'],
  'transaction_id': transaction_id,
  'passcode': passcode
}

response = requests.post(
             url, 
             json=payload, 
             headers={'Cookie': cookie}
           )

# Step 4: Obtain an authorization code
url = ('https://auth.tesla.com/oauth2/v3/authorize'
        + '?client_id=ownerapi'
        + '&code_challenge=' 
        + code_challenge
        + '&code_challenge_method=S256'
        + '&redirect_uri=' 
        + urllib.quote('https://auth.tesla.com/void/callback')
        + '&response_type=code'
        + '&scope=' 
        + urllib.quote('openid email offline_access')
        + '&state=state')
payload = {
  'transaction_id': transaction_id
}

response = requests.post(
             url, 
             data=payload, 
             allow_redirects=False, 
             headers={'Cookie': cookie}
           )

code = response.content[
         response.content.find('code') + 5: 
         response.content.find('&')
       ]
#print('code: ' + code)

# Step 5: Exchange authorization code for bearer token
url = 'https://auth.tesla.com/oauth2/v3/token'
payload = {
  'grant_type': 'authorization_code',
  'client_id': 'ownerapi',
  'code': code,
  'code_verifier': code_verifier,
  'redirect_uri': 'https://auth.tesla.com/void/callback'
}

response = requests.post(
             url, 
             json=payload, 
             headers={'Cookie': cookie}
           )

# Step 6: Exchange bearer token for access token
url = 'https://owner-api.teslamotors.com/oauth/token'
payload = {
  'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
  'client_id': '81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384',
  'client_secret': 'c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3'
}

response = requests.post(
             url, 
             json=payload, 
             headers={'authorization': 'Bearer ' 
                      + json.loads(response.text)['access_token']}
           ) 

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
  'values': [[str(datetime.datetime.fromtimestamp(
    json.loads(response.text)['created_at']
    + json.loads(response.text)['expires_in']
  ))]]
}]
service = GoogleAPI.getGoogleSheetService()
service.spreadsheets().values().batchUpdate(
  spreadsheetId=EV_SPREADSHEET_ID,
  body={'data': inputs, 'valueInputOption': 'USER_ENTERED'}
).execute()
service.close()


