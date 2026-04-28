from crontab import CronTab


##
# Script to clean up crontabs created for Tesla Climate and Charge Check.  
# Should be set to run in the middle of the day as all the crontabs are 
# evening or early morning.
#
# author: mjhwa@yahoo.com
##
def main():
  cron = CronTab(user='pi')
  job = cron.find_command('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/vehicle/climate.py --start=m3 >> /home/pi/tesla/python/cron.log 2>&1')
  cron.remove(job)
  cron.write()
  job = cron.find_command('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/vehicle/climate.py --stop=m3 >> /home/pi/tesla/python/cron.log 2>&1')
  cron.remove(job)
  cron.write()

  job = cron.find_command('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/vehicle/climate.py --start=mx >> /home/pi/tesla/python/cron.log 2>&1')
  cron.remove(job)
  cron.write()
  job = cron.find_command('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/vehicle/climate.py --stop=mx >> /home/pi/tesla/python/cron.log 2>&1')
  cron.remove(job)
  cron.write()

  job = cron.find_command('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/vehicle/charge.py --check=m3 >> /home/pi/tesla/python/cron.log 2>&1')
  cron.remove(job)
  cron.write()
  job = cron.find_command('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/vehicle/charge.py --check=mx >> /home/pi/tesla/python/cron.log 2>&1')
  cron.remove(job)
  cron.write()

if __name__ == "__main__":
  main()
