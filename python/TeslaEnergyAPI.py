import requests
import json
import configparser

from Logger import *
from datetime import timedelta, datetime

config = configparser.ConfigParser()
config.sections()
config.read('config.ini')
ACCESS_TOKEN = config['tesla']['access_token']
SITE_ID = config['energy']['site_id']


def getSiteStatus():
  try:
    url = ('https://owner-api.teslamotors.com/api/1/energy_sites/' 
           + SITE_ID 
           + '/site_status')

    response = json.loads(
      requests.get(
        url,
        headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
      ).text
    )

    for key in response['response']:
      print(str(key) + ' = ' + str(response['response'][key]))
  except Exception as e:
    logError('getSiteStatus(): ' + str(e))


def getSiteLiveStatus():
  try:
    url = ('https://owner-api.teslamotors.com/api/1/energy_sites/'
           + SITE_ID
           + '/live_status')

    response = json.loads(
      requests.get(
        url,
        headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
      ).text
    )

    for key in response['response']:
      print(str(key) + ' = ' + str(response['response'][key]))
  except Exception as e:
    logError('getSiteLiveStatus(): ' + str(e))


def getSiteInfo():
  try:
    url = ('https://owner-api.teslamotors.com/api/1/energy_sites/'
           + SITE_ID
           + '/site_info')

    response = json.loads(
      requests.get(
        url,
        headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
      ).text
    )

    for key, value in response['response'].items():
      #print(key + ' = ' + str(value))

      if key == 'user_settings':
        print(key)

        for key, value in response['response']['user_settings'].items():
          print('  ' 
                + key 
                + ' = ' 
                + str(value))

      if key == 'components':
        print(key)

        for key, value in response['response']['components'].items():
          print('  ' 
                + key 
                + ' = ' 
                + str(value))

      if key == 'tou_settings':
        print(key)

        for key, value in response['response']['tou_settings'].items():
          if key == 'schedule':
            print('  ' + key)
            for index, item in enumerate(
              response['response']['tou_settings']['schedule']
            ): 
              print('    ' + str(index + 1) + '. target' + ' = ' + item['target'])
              print('       week_days = ' + str(item['week_days']))
              print(
                '       start_seconds = ' 
                + str(
                  timedelta(
                    seconds=item['start_seconds']
                  )
                )
              )
              print(
                '       end_seconds = ' 
                + str(
                  timedelta(
                    seconds=item['end_seconds']
                  )
                )
              )
          else:
            print('  '
                  + key
                  + ' = '
                  + str(value))
      else:
        print(key + ' = ' + str(value))
  except Exception as e:
    logError('getSiteInfo(): ' + str(e))


def setBatteryModeBackup():
  setBatteryMode('backup')


def setBatteryModeSelfPowered():
  setBatteryMode('self_consumption')


def setBatteryModeAdvanced() {
  setBatteryMode('autonomous')


def setBatteryMode(mode):
  try:
    url = ('https://owner-api.teslamotors.com/api/1/energy_sites/' 
           + SITE_ID 
           + '/operation')
    payload = {
      'default_real_mode': mode
    }

    response = requests.post(
                 url,
                 json=payload,
                 headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
               )
  except Exception as e:
    logError('setBatteryMode( ' + mode + ' ): ' + str(e))


def setBatteryBackupReserve(backup_percent):
  try:
    url = ('https://owner-api.teslamotors.com/api/1/energy_sites/' 
           + SITE_ID 
           + '/backup')
    payload = {
      'backup_reserve_percent': backup_percent
    }

    response = requests.post(
                 url,
                 json=payload,
                 headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
               )
  except Exception as e:
    logError('setBatteryBackupReserve( ' + backup_percent + ' ): ' + str(e))


def main():
  getSiteInfo()

if __name__ == "__main__":
  main()
