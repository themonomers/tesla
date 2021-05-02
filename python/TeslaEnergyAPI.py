import requests
import json
import configparser
import os

from Crypto import decrypt
from Logger import logError
from datetime import timedelta, datetime
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
ACCESS_TOKEN = config['tesla']['access_token']
SITE_ID = config['energy']['site_id']
BATTERY_ID = config['energy']['battery_id']
buffer.close()


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

#    for key in response['response']:
#      print(str(key) + ' = ' + str(response['response'][key]))

    return response
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

#    for key in response['response']:
#      print(str(key) + ' = ' + str(response['response'][key]))

    return response
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

#    for key_1, value_1 in response['response'].items():
#      if (isinstance(value_1, dict) == True):
#        print(key_1)

#        for key_2, value_2 in response['response'][key_1].items():
#          if (isinstance(value_2, dict) == True):
#            print('  ' + key_2 + ' = ' + str(value_2))
#          elif (isinstance(value_2, list) == True):
#            print('  ' + key_2)

#            for index, item in enumerate(
#              response['response'][key_1][key_2]
#            ): 
#              print(
#                '    ' 
#                + str(index + 1) 
#                + '. week_days' 
#                + ' = ' 
#                + str(item['week_days'])
#              )
#              print('       target = ' + item['target'])
#              print(
#                '       start_seconds = ' 
#                + str(
#                  timedelta(
#                    seconds=item['start_seconds']
#                  )
#                )
#              )
#              print(
#                '       end_seconds = ' 
#                + str(
#                  timedelta(
#                    seconds=item['end_seconds']
#                  )
#                )
#              )
#          else:
#            print('  ' 
#              + key_2 
#              + ' = ' 
#              + str(value_2))
#      else:
#        print(key_1 + ' = ' + str(value_1))

    return response
  except Exception as e:
    logError('getSiteInfo(): ' + str(e))


def getSiteHistory(period):
  try:
    url = ('https://owner-api.teslamotors.com/api/1/energy_sites/' 
           + SITE_ID 
           + '/history?kind=energy&period='
           + period)

    response = json.loads(
      requests.get(
        url,
        headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
      ).text
    )

#    for key_1, value_1 in response['response'].items():
#      if (isinstance(value_1, list) == True):
#        print(key_1)

#        for i in range(len(response['response'][key_1])):
#          print('  timestamp = ' + response['response'][key_1][i]['timestamp'])

#          for key_2, value_2 in response['response'][key_1][i].items():
#            if (key_2 != 'timestamp'):
#              print('    ' + key_2 + ' = ' + str(value_2))
#      else:
#        print(key_1 + ' = ' + str(value_1))

    return response
  except Exception as e:
    logError('getSiteHistory(' + period + '): ' + str(e))


def getBatteryPowerHistory():
  try:
    url = ('https://owner-api.teslamotors.com/api/1/powerwalls/'
           + BATTERY_ID
           + '/powerhistory')

    response = json.loads(
      requests.get(
        url,
        headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
      ).text
    )

#    for key_1, value_1 in response['response'].items():
#      if (isinstance(value_1, list) == True):
#        print(key_1)

#        for i in range(len(response['response'][key_1])):
#          print('  timestamp = ' + response['response'][key_1][i]['timestamp'])

#          for key_2, value_2 in response['response'][key_1][i].items():
#            if (key_2 != 'timestamp'):
#              print('    ' + key_2 + ' = ' + str(value_2))
#      else:
#        print(key_1 + ' = ' + str(value_1))

    return response
  except Exception as e:
    logError('getBatteryPowerHistory(): ' + str(e))


##
# This API seems to be deprecated.
#
##
def getBatteryEnergyHistory():
  try:
    url = ('https://owner-api.teslamotors.com/api/1/powerwalls/'
           + BATTERY_ID
           + '/energyhistory')

    response = json.loads(
      requests.get(
        url,
        headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
      ).text
    )

    print(response)

    #for key_1, value_1 in response['response'].items():
    #  if (isinstance(value_1, list) == True):
    #    print(key_1)

    #    for i in range(len(response['response'][key_1])):
    #      print('  timestamp = ' + response['response'][key_1][i]['timestamp'])

    #      for key_2, value_2 in response['response'][key_1][i].items():
    #        if (key_2 != 'timestamp'):
    #          print('    ' + key_2 + ' = ' + str(value_2))
    #  else:
    #    print(key_1 + ' = ' + str(value_1))

    #return response
  except Exception as e:
    logError('getBatteryEnergyHistory(): ' + str(e))


def setBatteryModeBackup():
  setBatteryMode('backup')


def setBatteryModeSelfPowered():
  setBatteryMode('self_consumption')


def setBatteryModeAdvancedBalanced():
  setBatteryMode('autonomous')
  setEnergyTOUSettings('balanced')


def setBatteryModeAdvancedCost():
  setBatteryMode('autonomous')
  setEnergyTOUSettings('economics')


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
    logError('setBatteryMode(' + mode + '): ' + str(e))


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
    logError('setBatteryBackupReserve(' + backup_percent + '): ' + str(e))


def setEnergyTOUSettings(strategy):
  try:
    url = ('https://owner-api.teslamotors.com/api/1/energy_sites/'
           + SITE_ID
           + '/time_of_use_settings')
    payload = {
      'tou_settings': {
        'optimization_strategy': strategy,
        'schedule': [{
          'target': 'peak',
          'week_days': [1,2,3,4,5],
          'start_seconds': (16 * 60 * 60),
          'end_seconds': (21 * 60 * 60)
        },
        {
          'target': 'off_peak',
          'week_days': [1,2,3,4,5],
          'start_seconds': 0,
          'end_seconds': (15 * 60 * 60)
        },
        {
          'target': 'peak',
          'week_days': [0,6],
          'start_seconds': (16 * 60 * 60),
          'end_seconds': (21 * 60 * 60)
        },
        {
          'target': 'off_peak',
          'week_days': [0,6],
          'start_seconds': 0,
          'end_seconds': (15 * 60 * 60)
        }]
      }
    }

    response = requests.post(
                 url,
                 json=payload,
                 headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
               )
  except Exception as e:
    logError('setEnergyTOUSettings(' + strategy + '): ' + str(e))


def main():
  print('[1]  getSiteStatus()')
  print('[2]  getSiteLiveStatus()')
  print('[3]  getSiteInfo()')
  print('[4]  getSiteHistory()')
  print('[5]  getBatteryPowerHistory()')
  print('[6]  getBatteryEnergyHistory()')
  print('[7]  setBatteryModeBackup()')
  print('[8]  setBatteryModeSelfPowered()')
  print('[9]  setBatteryModeAdvancedBalanced()')
  print('[10] setBatteryModeAdvancedCost() \n')
  try:
    choice = int(raw_input('selection: '))
  except ValueError:
    return

  if choice == 1:
    getSiteStatus()
  elif choice == 2:
    getSiteLiveStatus()
  elif choice == 3:
    getSiteInfo()
  elif choice == 4:
    getSiteHistory('day')
  elif choice == 5:
    getBatteryPowerHistory()
  elif choice == 6:
    getBatteryEnergyHistory()
  elif choice == 7:
    setBatteryModeBackup()
  elif choice == 8:
    percent = float(raw_input('% battery reserve: '))
    setBatteryModeSelfPowered()
    setBatteryBackupReserve(percent)
  elif choice == 9:
    percent = float(raw_input('% battery reserve: '))
    setBatteryModeAdvancedBalanced()
    setBatteryBackupReserve(percent)
  elif choice == 10:
    percent = float(raw_input('% battery reserve: '))
    setBatteryModeAdvancedCost()
    setBatteryBackupReserve(percent)

if __name__ == "__main__":
  main()

