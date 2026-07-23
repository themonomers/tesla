import zoneinfo

from common.tokenutil import token
from common.configutil import (
  encrypted_config, 
  config,
  get_filepath)

# Vehicle
M3_VIN = encrypted_config['vehicle']['m3_vin']
MX_VIN = encrypted_config['vehicle']['mx_vin']
PRIMARY_LAT = float(encrypted_config['vehicle']['primary_lat'])
PRIMARY_LNG = float(encrypted_config['vehicle']['primary_lng'])
EV_SPREADSHEET_ID = encrypted_config['google']['ev_spreadsheet_id'] 
CHARGING_STATE_COMPLETE = 'Complete'

#Tesla
ACCESS_TOKEN = token['tesla']['access_token']
BASE_PROXY_URL = config['uri']['tesla_base_proxy_url']
CERT = get_filepath('tesla_cert')

# Notification
EMAIL_1 = encrypted_config['notification']['email_1']

# General
WAIT_TIME = 30
TIME_ZONE = config['general']['timezone']
PAC = zoneinfo.ZoneInfo(TIME_ZONE)