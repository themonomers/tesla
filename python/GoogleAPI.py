import os

from apiclient import discovery
from google.oauth2 import service_account


##
# Authenticates and returns a service to use methods for Google Sheets.
#
# author: mjhwa@yahoo.com
##
def getGoogleSheetService():
  try:
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    secret_file = os.path.join(os.getcwd(), 'gsheet_credentials.json')

    credentials = service_account.Credentials.from_service_account_file(
      secret_file, 
      scopes=scopes
    )
    service = discovery.build('sheets', 'v4', credentials=credentials)
    return service
  except Exception as e:
    print('getGoogleSheetService(): ' + str(e))


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
    print('findOpenRow(): ' + str(e))
