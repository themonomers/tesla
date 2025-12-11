from crontab import CronTab


##
# Script to clean up crontabs created for Tesla Smart Climate.  Should be 
# set to run in the middle of the day as all the crontabs are evening or 
# early morning.
#
# author: mjhwa@yahoo.com
##
def main():
  cron = CronTab(user='pi')
  job = cron.find_command('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/PreconditionM3Start.py >> /home/pi/tesla/python/cron.log 2>&1')
  cron.remove(job)
  cron.write()
  job = cron.find_command('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/PreconditionM3Stop.py >> /home/pi/tesla/python/cron.log 2>&1')
  cron.remove(job)
  cron.write()

  cron = CronTab(user='pi')
  job = cron.find_command('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/PreconditionMXStart.py >> /home/pi/tesla/python/cron.log 2>&1')
  cron.remove(job)
  cron.write()
  job = cron.find_command('/usr/bin/timeout -k 60 300 python -u /home/pi/tesla/python/PreconditionMXStop.py >> /home/pi/tesla/python/cron.log 2>&1')
  cron.remove(job)
  cron.write()

if __name__ == "__main__":
  main()
