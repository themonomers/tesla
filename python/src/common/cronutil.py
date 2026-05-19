import json

from pathlib import Path
from crontab import CronTab


##
# Crontab tools and retrieving configured cron job commands.
#
# author: mjhwa@yahoo.com
##
def get_cronjob(category, option=None): 
  # 1. Dynamically locate the project root relative to this script
  project_root = Path(__file__).resolve().parent.parent.parent

  # 2. Load configurations 
  config_path = project_root / './configs/cron.json'
  with open(config_path, "r") as f:
    config = json.load(f)

  if category == 'redirect':
    return config.get(category)
  else:
    return config.get('command').get(category).get(option)


##
# Removes crontab for a single command.
#
# author: mjhwa@yahoo.com
##
def delete_cron_tab(command):
  cron = CronTab(user='pi')
  job = cron.find_command(command)
  cron.remove(job)
  cron.write()


##
# Creates crontab entry for a single command.
#
# author: mjhwa@yahoo.com
##
def create_cron_tab(command, month, day, hour, minute):
  cron = CronTab(user='pi')
  job = cron.new(command=command)
  job.month.on(month)
  job.day.on(day)
  job.hour.on(hour)
  job.minute.on(minute)
  cron.write()