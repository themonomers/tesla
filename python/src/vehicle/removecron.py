from common.cronutil import delete_cron, get_cron


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
    delete_cron(get_cron('climate', 'start') + val + get_cron('redirect'))
    delete_cron(get_cron('climate', 'stop') + val + get_cron('redirect'))

    delete_cron(get_cron('charge', 'check') + val + get_cron('redirect'))

    delete_cron(get_cron('api', 'schedule_software_update') + val + get_cron('redirect'))


if __name__ == "__main__":
  main()