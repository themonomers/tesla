from common.cronutil import delete_cron_tab, get_cronjob


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
    delete_cron_tab(get_cronjob('climate', 'start') + val + get_cronjob('redirect'))
    delete_cron_tab(get_cronjob('climate', 'stop') + val + get_cronjob('redirect'))

    delete_cron_tab(get_cronjob('charge', 'check') + val + get_cronjob('redirect'))

    delete_cron_tab(get_cronjob('api', 'schedule_software_update') + val + get_cronjob('redirect'))


if __name__ == "__main__":
  main()