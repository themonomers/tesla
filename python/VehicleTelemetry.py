import time

from TeslaVehicleAPI import getVehicleData, wakeVehicle
from GoogleAPI import getGoogleSheetService, findOpenRow
from Email import sendEmail
from Utilities import getConfig
from Logger import logError
from datetime import datetime

config = getConfig()
M3_VIN = config['vehicle']['m3_vin']
MX_VIN = config['vehicle']['mx_vin']
EV_SPREADSHEET_ID = config['google']['ev_spreadsheet_id']
TELEMETRY_SHEET_ID = config['google']['telemetry_sheet_id']
EMAIL_1 = config['notification']['email_1']

WAIT_TIME = 30 


##
# Contains functions to read/write the vehicle's data, e.g. mileage, 
# efficiency, etc. into a Google Sheet for tracking, analysis, and graphs.
#
# author: mjhwa@yahoo.com
##
def writeM3Telemetry():
  try:
    # get rollup of vehicle data
    data = getVehicleData(M3_VIN)  
    
    inputs = []
    # write odometer value
    open_row = findOpenRow(EV_SPREADSHEET_ID, 'Telemetry','A:A')
    inputs.append({
      'range': 'Telemetry!A' + str(open_row),
      'values': [[data['response']['vehicle_state']['odometer']]]
    })
   
    # write date stamp
    inputs.append({
      'range': 'Telemetry!B' + str(open_row),
      'values': [[datetime.today().strftime('%B %d, %Y')]]
    })

    requests = []
    # copy mileage formulas down
    requests.append({
      'copyPaste': {
        'source': {
          'sheetId': TELEMETRY_SHEET_ID,
          'startRowIndex': 2,
          'endRowIndex': 3,
          'startColumnIndex': 2,
          'endColumnIndex': 7
        },
        'destination': {
          'sheetId': TELEMETRY_SHEET_ID,
          'startRowIndex': open_row - 2,
          'endRowIndex': open_row - 1,
          'startColumnIndex': 2,
          'endColumnIndex': 7
        },
        'pasteType': 'PASTE_NORMAL'
      }
    })

    # write max battery capacity
    inputs.append({
      'range': 'Telemetry!M' + str((open_row - 1)), 
      'values': [[(
        data['response']['charge_state']['battery_range']
        / (data['response']['charge_state']['battery_level'] 
           / 100.0)
      )]]
    })
    
    # copy down battery degradation % formula
    requests.append({
      'copyPaste': {
        'source': {
          'sheetId': TELEMETRY_SHEET_ID,
          'startRowIndex': 2,
          'endRowIndex': 3,
          'startColumnIndex': 13,
          'endColumnIndex': 14
        },
        'destination': {
          'sheetId': TELEMETRY_SHEET_ID,
          'startRowIndex': open_row - 2,
          'endRowIndex': open_row - 1,
          'startColumnIndex': 13,
          'endColumnIndex': 14
        },
        'pasteType': 'PASTE_NORMAL'
      }
    })

    # write target SoC %
    inputs.append({
      'range': 'Telemetry!O' + str(open_row), 
      'values': [[data['response']['charge_state']['charge_limit_soc']/100.0]]
    })
    
    # write data for efficiency calculation
    starting_range = (
      data['response']['charge_state']['battery_range']
      / (data['response']['charge_state']['battery_level'] 
         / 100.0) 
      * (data['response']['charge_state']['charge_limit_soc'] 
         / 100.0)
    )
    eod_range = data['response']['charge_state']['battery_range']
    
    # if the starting range is less than eod range or the car is not plugged 
    # in or charging state is complete, the starting range is equal to the 
    # eod range because it won't charge
    if (
      (starting_range < eod_range) 
      or (data['response']['charge_state']['charge_port_door_open'] == False) 
      or (data['response']['charge_state']['charging_state'] == 'Complete')
    ):
      starting_range = eod_range
    
    # write the starting_range for the next day   
    inputs.append({
      'range': 'Telemetry!H' + str(open_row), 
      'values': [[starting_range]]
    })
    inputs.append({
      'range': 'Telemetry!I' + str(open_row - 1), 
      'values': [[eod_range]]
    })
 
    # copy efficiency formulas down
    requests.append({
      'copyPaste': {
        'source': {
          'sheetId': TELEMETRY_SHEET_ID,
          'startRowIndex': 2,
          'endRowIndex': 3,
          'startColumnIndex': 9,
          'endColumnIndex': 12
        },
        'destination': {
          'sheetId': TELEMETRY_SHEET_ID,
          'startRowIndex': open_row - 2,
          'endRowIndex': open_row - 1,
          'startColumnIndex': 9,
          'endColumnIndex': 12
        },
        'pasteType': 'PASTE_NORMAL'
      }
    })
    
    # write temperature data into telemetry sheet
    inside_temp = (data['response']['climate_state']['inside_temp'] 
                   * 9/5 
                   + 32)  #convert to Fahrenheit
    outside_temp = (data['response']['climate_state']['outside_temp'] 
                    * 9/5 
                    + 32)

    inputs.append({
      'range': 'Telemetry!P' + str(open_row - 1), 
      'values': [[inside_temp]]
    })
    inputs.append({
      'range': 'Telemetry!Q' + str(open_row - 1), 
      'values': [[outside_temp]]
    })

    # write tire pressure data into telemetry sheet
    inputs.append({
      'range': 'Telemetry!R' + str(open_row - 1), 
      'values': [[data['response']['vehicle_state']['tpms_pressure_fl'] * 14.5038]]
    })
    inputs.append({
      'range': 'Telemetry!S' + str(open_row - 1), 
      'values': [[data['response']['vehicle_state']['tpms_pressure_fr'] * 14.5038]]
    })
    inputs.append({
      'range': 'Telemetry!T' + str(open_row - 1), 
      'values': [[data['response']['vehicle_state']['tpms_pressure_rl'] * 14.5038]]
    })
    inputs.append({
      'range': 'Telemetry!U' + str(open_row - 1), 
      'values': [[data['response']['vehicle_state']['tpms_pressure_rr'] * 14.5038]]
    })

    # batch write data and formula copies to sheet
    service = getGoogleSheetService()
    service.spreadsheets().values().batchUpdate(
      spreadsheetId=EV_SPREADSHEET_ID, 
      body={'data': inputs, 'valueInputOption': 'USER_ENTERED'}
    ).execute()
    service.spreadsheets().batchUpdate(
      spreadsheetId=EV_SPREADSHEET_ID, 
      body={'requests': requests}
    ).execute()
    service.close()
    
    # send email notification
    message = ('Model 3 telemetry successfully logged on ' 
               + datetime.today().strftime('%B %d, %Y %H:%M:%S') 
               + '.')
    sendEmail(EMAIL_1, 'Model 3 Telemetry Logged', message, '', '')
  except Exception as e:
    logError('writeM3Telemetry(): ' + str(e))


def writeMXTelemetry():
  try:
    # get rollup of vehicle data
    data = getVehicleData(MX_VIN)  
    
    inputs = []
    # write odometer value
    open_row = findOpenRow(EV_SPREADSHEET_ID, 'Telemetry','V:V')
    inputs.append({
      'range': 'Telemetry!V' + str(open_row),
      'values': [[data['response']['vehicle_state']['odometer']]]
    })
   
    # write date stamp
    inputs.append({
      'range': 'Telemetry!W' + str(open_row),
      'values': [[datetime.today().strftime('%B %d, %Y')]]
    })

    requests = []
    # copy mileage formulas down
    requests.append({
      'copyPaste': {
        'source': {
          'sheetId': TELEMETRY_SHEET_ID,
          'startRowIndex': 2,
          'endRowIndex': 3,
          'startColumnIndex': 23,
          'endColumnIndex': 28
        },
        'destination': {
          'sheetId': TELEMETRY_SHEET_ID,
          'startRowIndex': open_row - 2,
          'endRowIndex': open_row - 1,
          'startColumnIndex': 23,
          'endColumnIndex': 28
        },
        'pasteType': 'PASTE_NORMAL'
      }
    })

    # write max battery capacity
    inputs.append({
      'range': 'Telemetry!AH' + str((open_row - 1)), 
      'values': [[(
        data['response']['charge_state']['battery_range'] 
        / (data['response']['charge_state']['battery_level'] 
           / 100.0)
      )]]
    })
    
    # copy down battery degradation % formula
    requests.append({
      'copyPaste': {
        'source': {
          'sheetId': TELEMETRY_SHEET_ID,
          'startRowIndex': 2,
          'endRowIndex': 3,
          'startColumnIndex': 34,
          'endColumnIndex': 35
        },
        'destination': {
          'sheetId': TELEMETRY_SHEET_ID,
          'startRowIndex': open_row - 2,
          'endRowIndex': open_row - 1,
          'startColumnIndex': 34,
          'endColumnIndex': 35
        },
        'pasteType': 'PASTE_NORMAL'
      }
    })

    # write target SoC %
    inputs.append({
      'range': 'Telemetry!AJ' + str(open_row), 
      'values': [[data['response']['charge_state']['charge_limit_soc']/100.0]]
    })
    
    # write data for efficiency calculation
    starting_range = (
      data['response']['charge_state']['battery_range'] 
      / (data['response']['charge_state']['battery_level'] 
         / 100.0) 
      * (data['response']['charge_state']['charge_limit_soc']
         / 100.0))
    eod_range = data['response']['charge_state']['battery_range']
    
    # if the starting range is less than eod range or the car is not plugged 
    # in or charging state is complete, the starting range is equal to the 
    # eod range because it won't charge
    if (
      (starting_range < eod_range) 
      or (data['response']['charge_state']['charge_port_door_open'] == False) 
      or (data['response']['charge_state']['charging_state'] == 'Complete')
    ):
      starting_range = eod_range
    
    # write the starting_range for the next day   
    inputs.append({
      'range': 'Telemetry!AC' + str(open_row), 
      'values': [[starting_range]]
    })
    inputs.append({
      'range': 'Telemetry!AD' + str(open_row - 1), 
      'values': [[eod_range]]
    })
 
    # copy efficiency formulas down
    requests.append({
      'copyPaste': {
        'source': {
          'sheetId': TELEMETRY_SHEET_ID,
          'startRowIndex': 2,
          'endRowIndex': 3,
          'startColumnIndex': 30,
          'endColumnIndex': 33
        },
        'destination': {
          'sheetId': TELEMETRY_SHEET_ID,
          'startRowIndex': open_row - 2,
          'endRowIndex': open_row - 1,
          'startColumnIndex': 30,
          'endColumnIndex': 33
        },
        'pasteType': 'PASTE_NORMAL'
      }
    })
    
    # write temperature data into telemetry sheet
    inside_temp = (data['response']['climate_state']['inside_temp'] 
                   * 9/5 
                   + 32)  #convert to Fahrenheit
    outside_temp = (data['response']['climate_state']['outside_temp'] 
                    * 9/5 
                    + 32)

    inputs.append({
      'range': 'Telemetry!AK' + str(open_row - 1), 
      'values': [[inside_temp]]
    })
    inputs.append({
      'range': 'Telemetry!AL' + str(open_row - 1), 
      'values': [[outside_temp]]
    })

    # write tire pressure data into telemetry sheet
    inputs.append({
      'range': 'Telemetry!AM' + str(open_row - 1), 
      'values': [[data['response']['vehicle_state']['tpms_pressure_fl'] * 14.5038]]
    })
    inputs.append({
      'range': 'Telemetry!AN' + str(open_row - 1), 
      'values': [[data['response']['vehicle_state']['tpms_pressure_fr'] * 14.5038]]
    })
    inputs.append({
      'range': 'Telemetry!AO' + str(open_row - 1), 
      'values': [[data['response']['vehicle_state']['tpms_pressure_rl'] * 14.5038]]
    })
    inputs.append({
      'range': 'Telemetry!AP' + str(open_row - 1), 
      'values': [[data['response']['vehicle_state']['tpms_pressure_rr'] * 14.5038]]
    })

    # batch write data and formula copies to sheet
    service = getGoogleSheetService()
    service.spreadsheets().values().batchUpdate(
      spreadsheetId=EV_SPREADSHEET_ID, 
      body={'data': inputs, 'valueInputOption': 'USER_ENTERED'}
    ).execute()
    service.spreadsheets().batchUpdate(
      spreadsheetId=EV_SPREADSHEET_ID, 
      body={'requests': requests}
    ).execute()
    service.close()
    
    # send email notification
    message = ('Model X telemetry successfully logged on ' 
               + datetime.today().strftime('%B %d, %Y %H:%M:%S') 
               + '.')
    sendEmail(EMAIL_1, 'Model X Telemetry Logged', message, '', '')
  except Exception as e:
    logError('writeMXTelemetry(): ' + str(e))


##
# 
#
# author: mjhwa@yahoo.com
##
def main():
  writeM3Telemetry()
  writeMXTelemetry()

if __name__ == "__main__":
  main()

