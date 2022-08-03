import time

from TeslaVehicleAPI import getVehicleData, wakeVehicle, setScheduledCharging, stopChargeVehicle
from GoogleAPI import getGoogleSheetService
from SendEmail import sendEmail
from SmartClimate import setM3Precondition, setMXPrecondition
from Utilities import isVehicleAtHome, isVehicleAtNapa, getConfig
from Logger import logError
from datetime import datetime

config = getConfig()
M3_VIN = config['vehicle']['m3_vin']
MX_VIN = config['vehicle']['mx_vin']
EV_SPREADSHEET_ID = config['google']['ev_spreadsheet_id']
EMAIL_1 = config['notification']['email_1']
EMAIL_2 = config['notification']['email_2']

WAIT_TIME = 30 


##
# Writes to a Google Sheet that calculates optimum charging start times 
# for 2 vehicles to reach the target SoC by a time specified in the sheet.
#
# author: mjhwa@yahoo.com
##
def writeM3StartTimes(data):
  try:
    inputs = []

    # write m3 range to Google Sheet
    inputs.append({
      'range': 'Smart Charger!B10',
      'values': [[data['response']['charge_state']['battery_range']]]
    })

    # write m3 time and date stamp to Google Sheet
    inputs.append({
      'range': 'Smart Charger!D10',
      'values': [[(
        datetime.today().strftime('%H:%M:%S') 
        + ', ' 
        + datetime.today().strftime('%m/%d/%Y')
      )]]
    })
 
    # write m3 scheduled charge time to Google Sheet
    inputs.append({
      'range': 'Smart Charger!E28',
      'values': [[
        data['response']['charge_state']['scheduled_charging_start_time']
      ]]
    })
 
    # write m3 charge limit to Google Sheet
    inputs.append({
      'range': 'Smart Charger!B16',
      'values': [[data['response']['charge_state']['charge_limit_soc']/100.0]]
    })
 
    # write m3 max range
    inputs.append({
      'range': 'Smart Charger!B6',
      'values': [[(
        data['response']['charge_state']['battery_range'] 
        / (data['response']['charge_state']['battery_level'] 
           / 100.0)
      )]]
    })
 
    # batch write data to sheet
    service = getGoogleSheetService()
    service.spreadsheets().values().batchUpdate(
      spreadsheetId=EV_SPREADSHEET_ID, 
      body={'data': inputs, 'valueInputOption': 'USER_ENTERED'}
    ).execute()
  except Exception as e:
    logError('writeM3StartTimes(): ' + str(e))
  finally:
    service.close()


def writeMXStartTimes(data):
  try:
    inputs = []
 
    # write mx range to Google Sheet
    inputs.append({
      'range': 'Smart Charger!B9',
      'values': [[data['response']['charge_state']['battery_range']]]
    })

    # write mx time and date stamp to Google Sheet
    inputs.append({
      'range': 'Smart Charger!D9', 
      'values': [[(
        datetime.today().strftime('%H:%M:%S') 
        + ', ' 
        + datetime.today().strftime('%m/%d/%Y')
      )]]
    })
  
    # write mx scheduled charge time to Google Sheet
    inputs.append({
      'range': 'Smart Charger!F28', 
      'values': [[
        data['response']['charge_state']['scheduled_charging_start_time']
      ]]
    })
  
    # write mx charge limit to Google Sheet
    inputs.append({
      'range': 'Smart Charger!B15', 
      'values': [[data['response']['charge_state']['charge_limit_soc']/100.0]]
    })
  
    # write mx max range
    inputs.append({
      'range': 'Smart Charger!B5', 
      'values': [[(
        data['response']['charge_state']['battery_range'] 
        / (data['response']['charge_state']['battery_level'] 
           / 100.0)
      )]]
    })
  
    # batch write data to sheet
    service = getGoogleSheetService()
    service.spreadsheets().values().batchUpdate(
      spreadsheetId=EV_SPREADSHEET_ID, 
      body={'data': inputs, 'valueInputOption': 'USER_ENTERED'}
    ).execute()
  except Exception as e:
    logError('writeMXStartTimes(): ' + str(e))
  finally:
    service.close()


##
# Called by a crontab to read vehicle range and estimated charge 
# start time from a Google Sheet, then call the API to set a time 
# for scheduled charging in the vehicle.
#
# author: mjhwa@yahoo.com
##
def scheduleM3Charging(m3_data, mx_data): 
  try:
    service = getGoogleSheetService()

    target_soc = service.spreadsheets().values().get(
      spreadsheetId=EV_SPREADSHEET_ID, 
      range='Smart Charger!B18'
    ).execute().get('values', [])[0][0]
    current_soc = service.spreadsheets().values().get(
      spreadsheetId=EV_SPREADSHEET_ID, 
      range='Smart Charger!B10'
    ).execute().get('values', [])[0][0]

    # if the target SoC is greater than the current SoC and charging state isn't 
    # Complete, create a crontab for charging
    if (
      (target_soc > current_soc) 
      and (m3_data['response']['charge_state']['charging_state'] != 'Complete')
    ):
      # get calculated start time depending on location of cars
      if (
        (isVehicleAtHome(m3_data) == True) 
        and (isVehicleAtHome(mx_data) == True)
      ):
        start_time = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Charger!E26'
        ).execute().get('values', [])[0][0]
      elif (
        (isVehicleAtHome(m3_data) == True) 
        and (isVehicleAtHome(mx_data) == False)
      ):
        start_time = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Charger!J25'
        ).execute().get('values', [])[0][0]
      elif (isVehicleAtNapa(m3_data)):
        start_time = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Charger!J26'
        ).execute().get('values', [])[0][0]
      else:
        return

      minutes = start_time.split(':')
      total_minutes = (int(minutes[0]) * 60) + int(minutes[1])

      setScheduledCharging(M3_VIN, total_minutes)
      stopChargeVehicle(M3_VIN) # for some reason charging starts sometimes after scheduled charging API is called

      # send email notification
      message = ('The Model 3 is set to charge at ' 
                 + start_time 
                 + '.')
      sendEmail(EMAIL_1, 'Model 3 Set to Charge', message, '', '')
    service.close()
  except Exception as e:
    logError('scheduleM3Charging(): ' + str(e))


def scheduleMXCharging(m3_data, mx_data): 
  try:
    service = getGoogleSheetService()

    target_soc = service.spreadsheets().values().get(
      spreadsheetId=EV_SPREADSHEET_ID, 
      range='Smart Charger!B17'
    ).execute().get('values', [])[0][0]
    current_soc = service.spreadsheets().values().get(
      spreadsheetId=EV_SPREADSHEET_ID, 
      range='Smart Charger!B9'
    ).execute().get('values', [])[0][0]

    # if the target SoC is greater than the current SoC and charging state isn't 
    # Complete, schedule vehicle for charging
    if (
      (target_soc > current_soc) 
      and (mx_data['response']['charge_state']['charging_state'] != 'Complete')
    ):
      # get calculated start time depending on location of cars
      if (
        (isVehicleAtHome(mx_data) == True) 
        and (isVehicleAtHome(m3_data) == True)
      ):
        start_time = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Charger!F26'
        ).execute().get('values', [])[0][0]
      elif (
        (isVehicleAtHome(mx_data) == True) 
        and (isVehicleAtHome(m3_data) == False)
      ):
        start_time = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Charger!K26'
        ).execute().get('values', [])[0][0]
      elif (isVehicleAtNapa(mx_data)):
        start_time = service.spreadsheets().values().get(
          spreadsheetId=EV_SPREADSHEET_ID, 
          range='Smart Charger!K25'
        ).execute().get('values', [])[0][0]
      else:
        return

      minutes = start_time.split(':')
      total_minutes = (int(minutes[0]) * 60) + int(minutes[1])

      setScheduledCharging(MX_VIN, total_minutes)
      stopChargeVehicle(MX_VIN) # for some reason charging starts sometimes after scheduled charging API is called

      # send email notification
      message = ('The Model X is set to charge at ' 
                 + start_time 
                 + '.')
      sendEmail(EMAIL_1, 'Model X Set to Charge', message, '', '')
    service.close()
  except Exception as e:
    logError('scheduleMXCharging(): ' + str(e))


##
# Checks to see if the vehicles are plugged in, inferred from the charge 
# port door status, and sends an email to notify if it's not.  Also sets 
# scheduled charging time to start charging at the calculated date and time. 
# Skips if it's not within 0.25 miles from home.
#
# If one of the other cars is in Napa, set time charge start time based 
# on the alternate charge rate and set the charge start time for the one 
# at home to charge at full charge rate. 
#
# author: mjhwa@yahoo.com
##
def notifyIsTeslaPluggedIn():
  try:
    # get all vehicle data to avoid repeat API calls
    m3_data = getVehicleData(M3_VIN)
    mx_data = getVehicleData(MX_VIN)

    # write data to calculate charging start times; both functions for this needs 
    # to be executed, because the calculation on the Google Sheet is dependent on 
    # values from both vehicles
    writeM3StartTimes(m3_data)
    writeMXStartTimes(mx_data)

    # get car info
    charge_port_door_open = m3_data['response']['charge_state']['charge_port_door_open']
    battery_level = m3_data['response']['charge_state']['battery_level']
    battery_range = m3_data['response']['charge_state']['battery_range']

    service = getGoogleSheetService()
    email_notification = service.spreadsheets().values().get(
      spreadsheetId=EV_SPREADSHEET_ID, 
      range='Smart Charger!H10'
    ).execute().get('values', [])
    #print('email notify: ' + email_notification[0][0])
    
    # check if email notification is set to "on" first 
    if (email_notification[0][0] == 'on'):
      # send an email if the charge port door is not open, i.e. not plugged in
      if (charge_port_door_open == False):
        message = ('Your car is not plugged in.  \n\nCurrent battery level is ' 
                   + str(battery_level) 
                   + '%, ' 
                   + str(battery_range) 
                   + ' estimated miles.  \n\n-Your Model 3')
        sendEmail(EMAIL_1, 'Please Plug In Your Model 3', message, '', '')
        #print('send email: ' + message)

    charge_port_door_open = mx_data['response']['charge_state']['charge_port_door_open']
    battery_level = mx_data['response']['charge_state']['battery_level']
    battery_range = mx_data['response']['charge_state']['battery_range']

    email_notification = service.spreadsheets().values().get(
      spreadsheetId=EV_SPREADSHEET_ID, 
      range='Smart Charger!H9'
    ).execute().get('values', [])
    #print('email notify: ' + email_notification[0][0])
    service.close()

    # check if email notification is set to "on" first
    if (email_notification[0][0] == 'on'):
      # send an email if the charge port door is not open, i.e. not plugged in
      if (charge_port_door_open == False):
        message = ('Your car is not plugged in.  \n\nCurrent battery level is '
                   + str(battery_level) 
                   + '%, '
                   + str(battery_range) 
                   + ' estimated miles.  \n\n-Your Model X')
        sendEmail(EMAIL_2, 
                  'Please Plug In Your Model X', 
                  message, EMAIL_1, '')
        #print('send email: ' + message)

    # set set for scheduled charging
    scheduleM3Charging(m3_data, mx_data)
    scheduleMXCharging(m3_data, mx_data)

    # set cabin preconditioning the next morning
    setM3Precondition(m3_data)
    setMXPrecondition(mx_data)
  except Exception as e:
    logError('notifyIsTeslaPluggedIn(): ' + str(e))
    wakeVehicle(M3_VIN)
    wakeVehicle(MX_VIN)
    time.sleep(WAIT_TIME)
    notifyIsTeslaPluggedIn()


def main():
  notifyIsTeslaPluggedIn()

if __name__ == "__main__":
  main()

