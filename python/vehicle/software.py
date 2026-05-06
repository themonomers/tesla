import argparse
import zoneinfo

from common.utilities import (
  get_config, 
  delete_cron_tab, 
  create_cron_tab, 
  get_today_time,
  get_tomorrow_time,
  NewlineFormatter
)
from common.logger import log_error
from datetime import datetime

config = get_config()
M3_VIN = config['vehicle']['m3_vin']
MX_VIN = config['vehicle']['mx_vin']
TIME_ZONE = config['general']['timezone']
PAC = zoneinfo.ZoneInfo(TIME_ZONE)


##
# Mimics scheduling a software update from the vehicle interface 
# by using crontab.
#
# author: mjhwa@yahoo.com
##
def schedule_update(vin, time):
  try:
    if (vin == M3_VIN):
      delete_cron_tab('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/vehicle/api.py '
                      '--schedule_software_update=m3 >> /home/pi/tesla/python/cron.log 2>&1')
      create_cron_tab('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/vehicle/api.py '
                      '--schedule_software_update=m3 >> /home/pi/tesla/python/cron.log 2>&1', 
                      time.month, 
                      time.day, 
                      time.hour, 
                      time.minute)
    elif (vin == MX_VIN):
      delete_cron_tab('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/vehicle/api.py '
                      '--schedule_software_update=mx >> /home/pi/tesla/python/cron.log 2>&1')
      create_cron_tab('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/vehicle/api.py '
                      '--schedule_software_update=mx >> /home/pi/tesla/python/cron.log 2>&1', 
                      time.month, 
                      time.day, 
                      time.hour, 
                      time.minute)
  except Exception as e:
    log_error('schedule_update(' + vin + '):', e)


def main(parser):
  args = parser.parse_args()

  if (args.schedule_update):
    try:
      time_str = datetime.strptime(args.schedule_update[1], '%H:%M').strftime('%H:%M')
    except ValueError:
      parser.error(f"'{args.schedule_update[1]}' is not a valid time (HH:MM)")

    time = get_today_time(time_str)
    if (time < datetime.now().replace(tzinfo=PAC)):
      time = get_tomorrow_time(time_str)

    if args.schedule_update[0] == 'm3':
      schedule_update(M3_VIN, time)
    elif args.schedule_update[0] == 'mx':
      schedule_update(MX_VIN, time)
    else:
      parser.error('invalid VEHICLE type, must be \'m3\' or \'mx\'')
  else:
    parser.print_help()


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
                    prog='software.py',
                    description='Manage vehicle software.',
                    formatter_class=NewlineFormatter)
  group = parser.add_mutually_exclusive_group()
  group.add_argument(
#                     '-s', 
                     '--schedule_update', 
                     help='mimics scheduling a software update from the vehicle interface; VEHICLE can be \'m3\' or '
                          '\'mx\', TIME is in 24-hour format and if it\'s before the current time it will schedule it '
                          'for the following day',
                     nargs=2,
                     metavar=('VEHICLE', 'TIME')
                    )

  main(parser)