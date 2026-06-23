from common.utilities import delete_cron, config


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
    delete_cron(config['cron']['climate_start'] + val + ' ' + config['cron']['redirect'])
    delete_cron(config['cron']['climate_stop'] + val + ' ' + config['cron']['redirect'])

    delete_cron(config['cron']['charge_check'] + val + ' ' + config['cron']['redirect'])

    delete_cron(config['cron']['software_update'] + val + ' ' + config['cron']['redirect'])


if __name__ == "__main__":
  main()