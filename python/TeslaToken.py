import teslapy
import datetime
import zoneinfo

from datetime import datetime, timedelta

PAC = zoneinfo.ZoneInfo('America/Los_Angeles')

##
# Uses https://github.com/tdorssers/TeslaPy. To install, run:  
# python -m pip install teslapy
#
# Acquired tokens are stored in current working directory in 
# cache.json file for persistence by default.
##
with teslapy.Tesla('elon@tesla.com') as tesla:
    response = tesla.fetch_token()

expires_at = datetime.fromtimestamp(response['expires_at'], tz=PAC)

# print outputs to screen
print('[tesla]')
print('access_token=' + response['access_token'])
print('refresh_token=' + response['refresh_token'])
print('created_at=' + datetime.strftime(expires_at - timedelta(seconds = response['expires_in']), '%Y-%m-%d %H:%M:%S'))
print('expires_at=' + datetime.strftime(expires_at, '%Y-%m-%d %H:%M:%S'))
