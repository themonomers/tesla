from common.utilities import delete_cron_tab


##
# Script to clean up crontabs created for Tesla Climate, Charge Check, and
# Software Update.  Should be set to run in the middle of the day as all
# the crontabs are set for evening or early morning.
#
# author: mjhwa@yahoo.com
##
def main():
  values = ['m3', 'mx']

  for val in values:
    delete_cron_tab(f'/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/src/vehicle/climate.py --start={val} >> '
                    f'/home/pi/tesla/python/logs/cron.log 2>&1')
    delete_cron_tab(f'/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/src/vehicle/climate.py --stop={val} >> '
                    f'/home/pi/tesla/python/logs/cron.log 2>&1')

    delete_cron_tab(f'/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/src/vehicle/charge.py --check={val} >> '
                    f'/home/pi/tesla/python/logs/cron.log 2>&1')

    delete_cron_tab(f'/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/src/vehicle/api.py '
                    f'--schedule_software_update={val} >> /home/pi/tesla/python/logs/cron.log 2>&1')


if __name__ == "__main__":
  main()