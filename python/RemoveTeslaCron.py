from crontab import CronTab


##
#
#
# author: mjhwa@yahoo.com
##
def main():
  cron = CronTab(user='pi')
  job = cron.find_command('/home/pi/tesla/python/ChargeM3.py')
  cron.remove(job)
  cron.write()
  job = cron.find_command('/home/pi/tesla/python/ChargeM3Backup.py')
  cron.remove(job)
  cron.write()

  cron = CronTab(user='pi')
  job = cron.find_command('/home/pi/tesla/python/ChargeMX.py')
  cron.remove(job)
  cron.write()
  job = cron.find_command('/home/pi/tesla/python/ChargeMXBackup.py')
  cron.remove(job)
  cron.write()

  cron = CronTab(user='pi')
  job = cron.find_command('/home/pi/tesla/python/PreconditionM3Start.py')
  cron.remove(job)
  cron.write()
  job = cron.find_command('/home/pi/tesla/python/PreconditionM3Stop.py')
  cron.remove(job)
  cron.write()

  cron = CronTab(user='pi')
  job = cron.find_command('/home/pi/tesla/python/PreconditionMXStart.py')
  cron.remove(job)
  cron.write()
  job = cron.find_command('/home/pi/tesla/python/PreconditionMXStop.py')
  cron.remove(job)
  cron.write()

if __name__ == "__main__":
  main()
