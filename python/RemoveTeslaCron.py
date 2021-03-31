from crontab import CronTab

##
#
#
# author: mjhwa@yahoo.com
##
def main():
  cron = CronTab(user='pi')
  job = cron.find_command('/home/pi/tesla/ChargeM3.py')
  cron.remove(job)
  cron.write()
  job = cron.find_command('/home/pi/tesla/ChargeM3Backup.py')
  cron.remove(job)
  cron.write()

  cron = CronTab(user='pi')
  job = cron.find_command('/home/pi/tesla/ChargeMX.py')
  cron.remove(job)
  cron.write()
  job = cron.find_command('/home/pi/tesla/ChargeMXBackup.py')
  cron.remove(job)
  cron.write()

  cron = CronTab(user='pi')
  job = cron.find_command('/home/pi/tesla/PreconditionM3Start.py')
  cron.remove(job)
  cron.write()
  job = cron.find_command('/home/pi/tesla/PreconditionM3Stop.py')
  cron.remove(job)
  cron.write()

  cron = CronTab(user='pi')
  job = cron.find_command('/home/pi/tesla/PreconditionMXStart.py')
  cron.remove(job)
  cron.write()
  job = cron.find_command('/home/pi/tesla/PreconditionMXStop.py')
  cron.remove(job)
  cron.write()
  
if __name__ == "__main__":
  main()
