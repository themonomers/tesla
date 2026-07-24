import argparse

from common.utilities import (
  get_today_time, 
  get_tomorrow_time,
  delete_cron,
  create_cron)
from common.argutil import CustomHelpFormatter
from common.configutil import config
from common.constants import (
  M3_VIN,
  MX_VIN,
  PAC)
from datetime import datetime


##
# Mimics scheduling a software update from the vehicle interface 
# by using crontab.
#
# author: mjhwa@yahoo.com
##
def schedule_update(vin, time):
  delete_cron(config['cron']['software_update'] + ('m3' if vin == M3_VIN else 'mx') + ' ' + config['cron']['redirect'])
  create_cron(config['cron']['software_update'] + ('m3' if vin == M3_VIN else 'mx') + ' ' + config['cron']['redirect'], 
              time.month, 
              time.day, 
              time.hour, 
              time.minute)


def main(parser):
  args = parser.parse_args()

  if args.schedule_update:
    try:
      time_str = datetime.strptime(args.schedule_update[1], '%H:%M').strftime('%H:%M')
    except ValueError:
      parser.error(f"'{args.schedule_update[1]}' is not a valid time (HH:MM)")

    time = get_today_time(time_str)
    if time < datetime.now().replace(tzinfo=PAC):
      time = get_tomorrow_time(time_str)

    if args.schedule_update[0] == 'm3':
      schedule_update(M3_VIN, time)
    elif args.schedule_update[0] == 'mx':
      schedule_update(MX_VIN, time)
    else:
      parser.error('invalid VEHICLE type, must be \'m3\' or \'mx\'')
  else:
    parser.print_help()


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
                    prog='software.py',
                    description='Manage vehicle software.',
                    formatter_class=CustomHelpFormatter)
  group = parser.add_mutually_exclusive_group()
  group.add_argument(
                     '-s', 
                     '--schedule_update', 
                     help='mimics scheduling a software update from the vehicle interface; VEHICLE can be \'m3\' or '
                          '\'mx\', TIME is in 24-hour format and if it\'s before the current time it will schedule it '
                          'for the following day',
                     nargs=2,
                     metavar=('VEHICLE', 'TIME')
                    )

  main(parser)