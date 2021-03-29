import os

from apiclient import discovery
from google.oauth2 import service_account

##
# Authenticates and returns a service to use methods for Google Sheets.
#
# author: mjhwa@yahoo.com
##
def getGoogleSheetService():
  scopes = ['https://www.googleapis.com/auth/spreadsheets']
  secret_file = os.path.join(os.getcwd(), 'client_secret.json')

  credentials = service_account.Credentials.from_service_account_file(secret_file, scopes=scopes)
  service = discovery.build('sheets', 'v4', credentials=credentials)
  return service
