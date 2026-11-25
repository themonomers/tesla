import time
import argparse
import itertools
import string

from vehicle.api import get_vehicle_data
from common.googleutil import get_google_sheet_service, find_open_row
from common.emailutil import send_email
from common.utilities import bar_to_psi, celsius_to_fahrenheit
from common.argutil import CustomHelpFormatter
from common.logutil import log
from common.configutil import encrypted_config
from common.constants import (
  M3_VIN,
  MX_VIN,
  EV_SPREADSHEET_ID,
  WAIT_TIME,
  EMAIL_1,
  CHARGING_STATE_COMPLETE
)
from datetime import datetime

TELEMETRY_SHEET_ID = encrypted_config['google']['telemetry_sheet_id']
TELEMETRY_SHEET_NAME = 'Telemetry'
SHEET_PASTE_TYPE = 'PASTE_NORMAL'


def write_m3_telemetry():
  write_vehicle_data('Model 3', 'A', 2)


def write_mx_telemetry():
  write_vehicle_data('Model X', 'V', 23)


##
# Contains functions to read/write the vehicle's data, e.g. mileage, 
# efficiency, etc. into a Google Sheet for tracking, analysis, and graphs.
#
# author: mjhwa@yahoo.com
##
def write_vehicle_data(vehicle, start_letter, start_col_idx):
  try:
    while True:
      # get rollup of vehicle data
      data = get_vehicle_data(M3_VIN if vehicle == 'Model 3' else MX_VIN)

      # check for missing data and retry
      if any(x is None for x in get_check_list(data)):
        log().warning('Retry write_vehicle_data(), get_vehicle_data(%s) returned None for one or more values: %s', vehicle, data)
        time.sleep(WAIT_TIME)
        continue

      break

    inputs = []
    start_index = alpha_to_int(start_letter)
    # write odometer value
    open_row = find_open_row(EV_SPREADSHEET_ID, f'{TELEMETRY_SHEET_NAME}!{start_letter}:{start_letter}')
    inputs.append({
      'range': f'{TELEMETRY_SHEET_NAME}!{start_letter}{open_row}',
      'values': [[data['response']['vehicle_state']['odometer']]]
    })
   
    # write date stamp
    inputs.append({
      'range': f'{TELEMETRY_SHEET_NAME}!{int_to_alpha(start_index + 1)}{open_row}',
      'values': [[datetime.today().strftime('%B %d, %Y')]]
    })

    requests = []
    # copy formulas down: Day, Daily (mi), Daily Avg (mi), Days in Svc, Est Annual (mi)
    requests.append({
      'copyPaste': {
        'source': {
          'sheetId': TELEMETRY_SHEET_ID,
          'startRowIndex': 2,
          'endRowIndex': 3,
          'startColumnIndex': start_col_idx,
          'endColumnIndex': start_col_idx + 5
        },
        'destination': {
          'sheetId': TELEMETRY_SHEET_ID,
          'startRowIndex': open_row - 2,
          'endRowIndex': open_row - 1,
          'startColumnIndex': start_col_idx,
          'endColumnIndex': start_col_idx + 5
        },
        'pasteType': SHEET_PASTE_TYPE
      }
    })

    # write data for efficiency calculation
    starting_range = get_starting_range(data)
    eod_range = data['response']['charge_state']['battery_range']
    
    # if the starting range is less than eod range or the car is not plugged 
    # in or charging state is complete, the starting range is equal to the 
    # eod range because it won't charge
    if (
      starting_range < eod_range 
      or not data['response']['charge_state']['charge_port_door_open']
      or data['response']['charge_state']['charging_state'] == CHARGING_STATE_COMPLETE
    ):
      starting_range = eod_range
    
    # write the starting_range for the next day   
    inputs.append({
      'range': f'{TELEMETRY_SHEET_NAME}!{int_to_alpha(start_index + 7)}{open_row}',
      'values': [[starting_range]]
    })
    inputs.append({
      'range': f'{TELEMETRY_SHEET_NAME}!{int_to_alpha(start_index + 8)}{open_row - 1}',
      'values': [[eod_range]]
    })

    # copy formulas down: Range Used (mi), Efficiency, Energy Use (Wh/ mi)
    requests.append({
      'copyPaste': {
        'source': {
          'sheetId': TELEMETRY_SHEET_ID,
          'startRowIndex': 2,
          'endRowIndex': 3,
          'startColumnIndex': start_col_idx + 7,
          'endColumnIndex': start_col_idx + 10
        },
        'destination': {
          'sheetId': TELEMETRY_SHEET_ID,
          'startRowIndex': open_row - 2,
          'endRowIndex': open_row - 1,
          'startColumnIndex': start_col_idx + 7,
          'endColumnIndex': start_col_idx + 10
        },
        'pasteType': SHEET_PASTE_TYPE
      }
    })

    # write max battery capacity
    inputs.append({
      'range': f'{TELEMETRY_SHEET_NAME}!{int_to_alpha(start_index + 12)}{open_row - 1}',
      'values': [[get_battery_capacity(data)]]
    })
    
    # copy formulas down: Battery Degradation
    requests.append({
      'copyPaste': {
        'source': {
          'sheetId': TELEMETRY_SHEET_ID,
          'startRowIndex': 2,
          'endRowIndex': 3,
          'startColumnIndex': start_col_idx + 11,
          'endColumnIndex': start_col_idx + 12
        },
        'destination': {
          'sheetId': TELEMETRY_SHEET_ID,
          'startRowIndex': open_row - 2,
          'endRowIndex': open_row - 1,
          'startColumnIndex': start_col_idx + 11,
          'endColumnIndex': start_col_idx + 12
        },
        'pasteType': SHEET_PASTE_TYPE
      }
    })

    # write target SoC %
    inputs.append({
      'range': f'{TELEMETRY_SHEET_NAME}!{int_to_alpha(start_index + 14)}{open_row}',
      'values': [[data['response']['charge_state']['charge_limit_soc'] / 100.0]]
    })
    
    # write temperature data into telemetry sheet
    inside_temp = celsius_to_fahrenheit(data['response']['climate_state']['inside_temp'])
    outside_temp = celsius_to_fahrenheit(data['response']['climate_state']['outside_temp'])

    inputs.append({
      'range': f'{TELEMETRY_SHEET_NAME}!{int_to_alpha(start_index + 15)}{open_row - 1}',
      'values': [[inside_temp]]
    })
    inputs.append({
      'range': f'{TELEMETRY_SHEET_NAME}!{int_to_alpha(start_index + 16)}{open_row - 1}',
      'values': [[outside_temp]]
    })

    # write tire pressure data into telemetry sheet
    inputs.append({
      'range': f'{TELEMETRY_SHEET_NAME}!{int_to_alpha(start_index + 17)}{open_row - 1}',
      'values': [[bar_to_psi(data['response']['vehicle_state']['tpms_pressure_fl'])]]
    })
    inputs.append({
      'range': f'{TELEMETRY_SHEET_NAME}!{int_to_alpha(start_index + 18)}{open_row - 1}',
      'values': [[bar_to_psi(data['response']['vehicle_state']['tpms_pressure_fr'])]]
    })
    inputs.append({
      'range': f'{TELEMETRY_SHEET_NAME}!{int_to_alpha(start_index + 19)}{open_row - 1}',
      'values': [[bar_to_psi(data['response']['vehicle_state']['tpms_pressure_rl'])]]
    })
    inputs.append({
      'range': f'{TELEMETRY_SHEET_NAME}!{int_to_alpha(start_index + 20)}{open_row - 1}',
      'values': [[bar_to_psi(data['response']['vehicle_state']['tpms_pressure_rr'])]]
    })

    # batch write data and formula copies to sheet
    service = get_google_sheet_service()
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
    message = f'{vehicle} telemetry successfully logged on {datetime.today():%B %d, %Y %H:%M:%S}.'
    send_email(f'{vehicle} Telemetry Logged', message, EMAIL_1)
  except Exception as e:
    log().error('write_vehicle_data(%s): %s', vehicle, e, exc_info=True)


##
# Convert a letter to its integer based alphabet position, 
# starting with A = 1.
#
# author: mjhwa@yahoo.com
##
def alpha_to_int(letters):
  result = 0
  for char in letters.upper():
    result = result * 26 + (ord(char) - ord('A') + 1)

  return result - 1


##
# Converts alphabet integer(s) position (A = 1) back to a letter 
# or letters for incrementing purposes while also allowing 
# for wrapping around Z to AA, etc. for continuous incrementing
# as used in spreadsheet columns.
#
# author: mjhwa@yahoo.com
##
def int_to_alpha(start_index):
  alphabet = string.ascii_uppercase
  for num in itertools.count(start_index):
    chars = []
    n = num
    while n >= 0:
      chars.append(alphabet[n % 26])
      n = (n // 26) - 1
    return ''.join(reversed(chars))


##
# List of data points to check for missing data in the vehicle response. 
#
# author: mjhwa@yahoo.com
##
def get_check_list(data):
  return [
    data["response"]["charge_state"]["battery_range"],
    data["response"]["charge_state"]["battery_level"],
    data['response']['charge_state']['charge_limit_soc'],
    data['response']['climate_state']['inside_temp'],
    data['response']['climate_state']['outside_temp'],
    data['response']['vehicle_state']['tpms_pressure_fl'],
    data['response']['vehicle_state']['tpms_pressure_fr'],
    data['response']['vehicle_state']['tpms_pressure_rl'],
    data['response']['vehicle_state']['tpms_pressure_rr']
  ]


def get_battery_capacity(data):
  return (
    data['response']['charge_state']['battery_range']
    / (data['response']['charge_state']['battery_level'] / 100.0)
  )


def get_starting_range(data):
  return (
    data['response']['charge_state']['battery_range']
    / (data['response']['charge_state']['battery_level'] / 100.0) 
    * (data['response']['charge_state']['charge_limit_soc'] / 100.0)
  )


def main(parser):
  args = parser.parse_args()

  if args.write_all:
    write_m3_telemetry()
    write_mx_telemetry()
  elif args.write_vehicle:
    if args.write_vehicle[0] == 'm3':
      write_m3_telemetry()
    elif args.write_vehicle[0] == 'mx':
      write_mx_telemetry()
    else:
      parser.error('invalid VEHICLE type, must be \'m3\' or \'mx\'')
  else:
    parser.print_help()


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
    prog='telemetry.py',
    description='Read/write the vehicle data into a Google Sheet for tracking, analysis, and graphs.',
    formatter_class=CustomHelpFormatter
  )
  group = parser.add_mutually_exclusive_group()
  group.add_argument(
    '-a', 
    '--write_all', 
    help='writes telemetry for all vehicles',
    action='store_true'
  )
  group.add_argument(
    '-v', 
    '--write_vehicle', 
    help='writes telemetry for a specific vehicle; VEHICLE can be \'m3\' or '
         '\'mx\'',
    nargs=1,
    metavar='VEHICLE'
  )

  main(parser)