from __future__ import print_function

import os
import Logger

from apiclient import discovery
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


##
# Authenticates and returns a service to use methods for Google Sheets.
#
# author: mjhwa@yahoo.com
##
def getGoogleSheetService():
  try:
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    secret_file = (
      os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 
        'gsheet_credentials.json'
      )
    )

    credentials = service_account.Credentials.from_service_account_file(
      secret_file, 
      scopes=scopes
    )
    service = discovery.build('sheets', 'v4', credentials=credentials)
    return service
  except Exception as e:
    Logger.logError('getGoogleSheetService(): ' + str(e))


##
# Looks for the next empty cell in a Google Sheet row to avoid overwriting data
# when reading/writing values.
#
# author: mjhwa@yahoo.com
##
def findOpenRow(sheet_id, sheet_name, range):
  try:
    service = getGoogleSheetService()
    range = sheet_name + '!' + range
    values = service.spreadsheets().values().get(
      spreadsheetId=sheet_id,
      range=range
    ).execute().get('values', [])
    service.close()

    if (values == False):
      return 1

    return len(values) + 1
  except Exception as e:
    Logger.logError('findOpenRow(): ' + str(e))


##
# Authenticates and returns a service to use methods for Google Mail.
#
# author: mjhwa@yahoo.com
##
def getGoogleMailService():
  try:
    # If modifying these scopes, delete the file token.json.
    scopes = ['https://www.googleapis.com/auth/gmail.modify']

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(
      os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 
        'token.json'
      )
    ):
      creds = Credentials.from_authorized_user_file(
        os.path.join(
          os.path.dirname(os.path.abspath(__file__)), 
          'token.json'
        ), 
        scopes
      )

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
      if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
      else:
        flow = InstalledAppFlow.from_client_secrets_file(
          os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            'client_secret.json'
          ), 
          scopes,
          redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
        )

        # Tell the user to go to the authorization URL.
        # The user will get an authorization code. This code is used to get the
        # access token.
        print('Please go to this URL: ')
        auth_url, _ = flow.authorization_url(prompt='consent')
        creds = flow.run_console(format(auth_url))

      # Save the credentials for the next run
      with open(
        os.path.join(
          os.path.dirname(os.path.abspath(__file__)), 
          'token.json'
        ), 
        'w'
      ) as token:
        token.write(creds.to_json())
        token.close()

    return build('gmail', 'v1', credentials=creds)
  except Exception as e:
    Logger.logError('getGoogleMailService(): ' + str(e))


