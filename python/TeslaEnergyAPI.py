import requests
import json
import pytz

from Logger import logError
from Utilities import printJson, getConfig, getToken
from datetime import datetime

ACCESS_TOKEN = getToken()['tesla']['access_token']
config = getConfig()
SITE_ID = config['energy']['site_id']
BATTERY_ID = config['energy']['battery_id']
BASE_OWNER_URL = config['tesla']['base_owner_url']
TIME_ZONE = config['general']['timezone']


##
# Gets some quick and basic information.
#
# author: mjhwa@yahoo.com
##
def getSiteStatus():
  try:
    url = (BASE_OWNER_URL
           + '/energy_sites/' 
           + SITE_ID 
           + '/site_status')

    response = json.loads(
      requests.get(
        url,
        headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
      ).text
    )

    return response
  except Exception as e:
    logError('getSiteStatus(): ' + str(e))


##
# Gets more information as well as live data such as solar production.
#
# author: mjhwa@yahoo.com
##
def getSiteLiveStatus():
  try:
    url = (BASE_OWNER_URL
           + '/energy_sites/' 
           + SITE_ID
           + '/live_status')

    response = json.loads(
      requests.get(
        url,
        headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
      ).text
    )

    return response
  except Exception as e:
    logError('getSiteLiveStatus(): ' + str(e))


##
# Gets detailed information.
#
# author: mjhwa@yahoo.com
##
def getSiteInfo():
  try:
    url = (BASE_OWNER_URL
           + '/energy_sites/' 
           + SITE_ID
           + '/site_info')

    response = json.loads(
      requests.get(
        url,
        headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
      ).text
    )

    return response
  except Exception as e:
    logError('getSiteInfo(): ' + str(e))


##
# Gets summary level information about energy imports and exports down to the
# day.
#
# author: mjhwa@yahoo.com
##
def getSiteHistory(period, date):
  try:
    local = pytz.timezone(TIME_ZONE)
    date = local.localize(datetime(
      date.year, 
      date.month, 
      date.day, 
      23, 
      59, 
      59, 
      0
    ), is_dst=None)

    url = (BASE_OWNER_URL
           + '/energy_sites/' 
           + SITE_ID 
           + '/history'
           + '?kind=energy'
           + '&end_date=' 
           + datetime.strftime(date.astimezone(pytz.utc), '%Y-%m-%dT%H:%M:%SZ')
           + '&period=' + period)

    response = json.loads(
      requests.get(
        url,
        headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
      ).text
    )

    return response
  except Exception as e:
    logError('getSiteHistory(' + period + '): ' + str(e))


##
# Get grid outage/battery backup events.
#
# author: mjhwa@yahoo.com
##
def getBatteryBackupHistory():
  try:
    url = (BASE_OWNER_URL
           + '/energy_sites/' 
           + SITE_ID 
           + '/history?kind=backup')

    response = json.loads(
      requests.get(
        url,
        headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
      ).text
    )

    return response
  except Exception as e:
    logError('getBatteryBackupHistory(): ' + str(e))


##
# Gets summary level information about energy imports and exports down to the
# day, separated by time of use.
#
# author: mjhwa@yahoo.com
##
def getSiteTOUHistory(period, date):
  try:
    local = pytz.timezone(TIME_ZONE)
    s_date = local.localize(datetime(
      date.year,
      date.month,
      date.day,
      0,
      0,
      0,
      0
    ), is_dst=None)

    e_date = local.localize(datetime(
      date.year,
      date.month,
      date.day,
      23,
      59,
      59,
      0
    ), is_dst=None)

    url = (BASE_OWNER_URL
           + '/energy_sites/' 
           + SITE_ID
           + '/calendar_history'
           + '?kind=time_of_use_energy'
           + '&period=' + period
           + '&start_date=' 
           + datetime.strftime(
               s_date.astimezone(pytz.utc), 
               '%Y-%m-%dT%H:%M:%SZ')
           + '&end_date=' 
           + datetime.strftime(
               e_date.astimezone(pytz.utc), 
               '%Y-%m-%dT%H:%M:%SZ')
          )

    response = json.loads(
      requests.get(
        url,
        headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
      ).text
    )
 
    return response
  except Exception as e:
    logError('getSiteTOUHistory(): ' + str(e))


##
# Gets the historic battery charge level data in 15 minute increments that's
# shown on the mobile app. 
#
# author: mjhwa@yahoo.com
##
def getBatteryChargeHistory(period, date):
  try:
    local = pytz.timezone(TIME_ZONE)
    date = local.localize(datetime(
      date.year,
      date.month,
      date.day,
      23,
      59,
      59,
      0
    ), is_dst=None)

    url = (BASE_OWNER_URL
           + '/energy_sites/' 
           + SITE_ID 
           + '/calendar_history'
           + '?kind=soe'
           + '&period=' + period
           + '&end_date='
           + datetime.strftime(date.astimezone(pytz.utc), '%Y-%m-%dT%H:%M:%SZ')
          )

    response = json.loads(
      requests.get(
        url,
        headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
      ).text
    )

    return response
  except Exception as e:
    logError('getBatteryChargeHistory(): ' + str(e))


##
# Gets energy information in 5 minute increments, with ability to query by 
# date.  Used to create the "ENERGY USAGE" charts in the mobile app.
#
# author: mjhwa@yahoo.com
##
def getPowerHistory(period, date):
  try:
    local = pytz.timezone(TIME_ZONE)
    s_date = local.localize(datetime(
      date.year,
      date.month,
      date.day,
      0,
      0,
      0,
      0
    ), is_dst=None)

    e_date = local.localize(datetime(
      date.year,
      date.month,
      date.day,
      23,
      59,
      59,
      0
    ), is_dst=None)

    url = (BASE_OWNER_URL
           + '/energy_sites/' 
           + SITE_ID
           + '/calendar_history'
           + '?kind=power'
           + '&start_date='
           + datetime.strftime(
               s_date.astimezone(pytz.utc), 
               '%Y-%m-%dT%H:%M:%SZ')
           + '&end_date='
           + datetime.strftime(
               e_date.astimezone(pytz.utc), 
               '%Y-%m-%dT%H:%M:%SZ')
           + '&period=' + period)

    response = json.loads(
      requests.get(
        url,
        headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
      ).text
    )

    return response
  except Exception as e:
    logError('getPowerHistory(): ' + str(e))


##
# Lists all rate tariffs available in the mobile app.
#
# author: mjhwa@yahoo.com
##
def getRateTariffs():
  try:
    url = (BASE_OWNER_URL
           + '/energy_sites/' 
           + 'rate_tariffs')

    response = json.loads(
      requests.get(
        url,
        headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
      ).text
    )

    return response
  except Exception as e:
    logError('getRateTariffs(): ' + str(e))


##
# Lists the tariff selected for your site in the mobile
# app along with published rates, TOU schedules, etc.
#
# author: mjhwa@yahoo.com
##
def getSiteTariff():
  try:
    url = (BASE_OWNER_URL
           + '/energy_sites/' 
           + SITE_ID
           + '/tariff_rate')

    response = json.loads(
      requests.get(
        url,
        headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
      ).text
    )

    return response
  except Exception as e:
    logError('getSiteTariff(): ' + str(e))


##
# Retrieves the estimated time remaining in the powerwall(s).
#
# author: mjhwa@yahoo.com
##
def getBackupTimeRemaining():
  try:
    url = (BASE_OWNER_URL
           + '/energy_sites/' 
           + SITE_ID
           + '/backup_time_remaining')

    response = json.loads(
      requests.get(
        url,
        headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
      ).text
    )

    return response
  except Exception as e:
    logError('getBackupTimeRemaining(): ' + str(e))


##
# Gets the data for Solar Value in the mobile app to show estimated 
# cost savings.  
#
# author: mjhwa@yahoo.com
##
def getSavingsForecast(period, date):
  try:
    local = pytz.timezone(TIME_ZONE)
    s_date = local.localize(datetime(
      date.year,
      date.month,
      date.day,
      0,
      0,
      0,
      0
    ), is_dst=None)

    e_date = local.localize(datetime(
      date.year,
      date.month,
      date.day,
      23,
      59,
      59,
      0
    ), is_dst=None)

    url = (BASE_OWNER_URL
           + '/energy_sites/' 
           + SITE_ID
           + '/calendar_history'
           + '?kind=savings'
           + '&period=' + period
           + '&start_date=' 
           + datetime.strftime(
               s_date.astimezone(pytz.utc),
               '%Y-%m-%dT%H:%M:%SZ')
           + '&end_date=' 
           + datetime.strftime(
               e_date.astimezone(pytz.utc),
               '%Y-%m-%dT%H:%M:%SZ')
           + '&tariff=PGE-EV2-A'
          )

    response = json.loads(
      requests.get(
        url,
        headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
      ).text
    )

    return response
  except Exception as e:
    logError('getSavingsForecast(): ' + str(e))


##
# Changes Operational Mode in the mobile app to "Backup-only".
# This doesn't appear to be any setting in the mobile app
# but this API call still forces the system to only use the 
# battery in an outage.  This also has a side effect of hiding
# the Time of Use card as well as returns an empty response
# when calling the API for Time of Use data.
#
# author: mjhwa@yahoo.com
##
def setOperationalModeBackup():
  return setOperationalMode('backup')


##
# Changes Operational Mode in the mobile app to "Self-Powered".
#
# author: mjhwa@yahoo.com
##
def setOperationalModeSelfPowered():
  return setOperationalMode('self_consumption')


##
# Changes Operational Mode in the mobile app to "Time-Based Control".
#
# author: mjhwa@yahoo.com
##
def setOperationalModeTimeBasedControl():
  return setOperationalMode('autonomous')


##
# Changes Energy Exports in the mobile app to "Everything".
# Defaults Grid Charging setting to "No".
#
# author: mjhwa@yahoo.com
##
def setEnergyExportsEverything():
  return setGridImportExport('battery_ok', True)


##
# Changes Energy Exports in the mobile app to "Solar".
# Defaults Grid Charging setting to "No".
#
# author: mjhwa@yahoo.com
##
def setEnergyExportsSolar():
  return setGridImportExport('pv_only', True)


##
# Changes Operational Mode setting in the mobile app. 
#
# author: mjhwa@yahoo.com
##
def setOperationalMode(mode):
  try:
    url = (BASE_OWNER_URL
           + '/energy_sites/' 
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

    return response
  except Exception as e:
    logError('setOperationalMode(' + mode + '): ' + str(e))


##
# Changes Energy Exports and Grid Charging settings in the mobile app.
#
# author: mjhwa@yahoo.com
##
def setGridImportExport(export_rule, disallow_grid_charging):
  try:
    url = (BASE_OWNER_URL
           + '/energy_sites/' 
           + SITE_ID
           + '/grid_import_export')
    
    payload = {
      'customer_preferred_export_rule': export_rule,
      'disallow_charge_from_grid_with_solar_installed': disallow_grid_charging
    }

    response = requests.post(
                 url,
                 json=payload,
                 headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
               )

    return response
  except Exception as e:
    logError('setGridImportExport(' + export_rule + ', ' + disallow_grid_charging + '): ' + str(e))


##
# Sets "Reserve Energy for Grid Outages", % Backup, in the mobile app.
#
# author: mjhwa@yahoo.com
##
def setBackupReserve(backup_percent):
  try:
    url = (BASE_OWNER_URL
           + '/energy_sites/' 
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

    return response
  except Exception as e:
    logError('setBackupReserve(' + backup_percent + '): ' + str(e))


##
# Sets off grid vehicle charging reserve % to save for home use.
# It seems the maximum is 95% so 5% is the minimum to share with vehicle.
#
# author: mjhwa@yahoo.com
##
def setOffGridVehicleChargingReserve(percent):
  try:
    url = (BASE_OWNER_URL
           + '/energy_sites/' 
           + SITE_ID 
           + '/off_grid_vehicle_charging_reserve')
    
    payload = {
      'off_grid_vehicle_charging_reserve_percent': percent
    }

    response = requests.post(
                 url,
                 json=payload,
                 headers={'authorization': 'Bearer ' + ACCESS_TOKEN}
               )

    return response
  except Exception as e:
    logError('setOffGridVehicleChargingReserve(' + percent + '): ' + str(e))


def main():
  print('[1]  getSiteStatus()')
  print('[2]  getSiteLiveStatus()')
  print('[3]  getSiteInfo()')
  print('[4]  getSiteHistory()')
  print('[5]  getBatteryBackupHistory()')
  print('[6]  getSiteTOUHistory()')
  print('[7]  getBatteryChargeHistory()')
  print('[8]  getPowerHistory()')
  print('[9]  getRateTariffs()')
  print('[10] getSiteTariff()')
  print('[11] getBackupTimeRemaining()')
  print('[12] getSavingsForecast()')
  print('[13] setOperationalModeBackup()')
  print('[14] setOperationalModeSelfPowered()')
  print('[15] setOperationalModeTimeBasedControl()')
  print('[16] setEnergyExportsEverything()')
  print('[17] setEnergyExportsSolar()')
  print('[18] setBackupReserve()')
  print('[19] setOffGridVehicleChargingReserve()')

  try:
    choice = int(input('selection: '))
  except ValueError:
    return

  if choice == 1:
    data = getSiteStatus()
  elif choice == 2:
    data = getSiteLiveStatus()
  elif choice == 3:
    data = getSiteInfo()
  elif choice == 4:
    date = input('date(m/d/yyyy): ')
    date = datetime.strptime(date, '%m/%d/%Y')
    data = getSiteHistory('day', date)
  elif choice == 5:
    data = getBatteryBackupHistory()
  elif choice == 6:
    date = input('date(m/d/yyyy): ')
    date = datetime.strptime(date, '%m/%d/%Y')
    data = getSiteTOUHistory('day', date)
  elif choice == 7:
    date = input('date(m/d/yyyy): ')
    date = datetime.strptime(date, '%m/%d/%Y')
    data = getBatteryChargeHistory('day', date)
  elif choice == 8:
    date = input('date(m/d/yyyy): ')
    date = datetime.strptime(date, '%m/%d/%Y')
    data = getPowerHistory('day', date)
  elif choice == 9:
    data = getRateTariffs()
  elif choice == 10:
    data = getSiteTariff()
  elif choice == 11:
    data = getBackupTimeRemaining()
  elif choice == 12:
    date = input('date(m/d/yyyy): ')
    date = datetime.strptime(date, '%m/%d/%Y')
    data = getSavingsForecast('day', date)
  elif choice == 13:
    setOperationalModeBackup()
  elif choice == 14:
    setOperationalModeSelfPowered()
  elif choice == 15:
    setOperationalModeTimeBasedControl()
  elif choice == 16:
    setEnergyExportsEverything()
  elif choice == 17:
    setEnergyExportsSolar()
  elif choice == 18:
    percent = float(input('% for backup use: '))
    data = setBackupReserve(percent)
  elif choice == 19:
    percent = float(input('% save for home use: '))
    data = setOffGridVehicleChargingReserve(percent)
  
  printJson(data, 0)


if __name__ == "__main__":
  main()
