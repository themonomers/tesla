import configparser
import os

from datetime import datetime, date, timedelta
from Utilities import getDailyWeather
from TeslaEnergyAPI import setBatteryModeBackup, setBatteryModeAdvancedCost, setBatteryBackupReserve
from SendEmail import sendEmail
from Crypto import decrypt
from Logger import logError
from io import StringIO

buffer = StringIO(
  decrypt(
    os.path.join(
      os.path.dirname(os.path.abspath(__file__)),
      'config.rsa'
    )
  ).decode('utf-8')
)
config = configparser.ConfigParser()
config.sections()
config.readfp(buffer)
HOME_LAT = float(config['vehicle']['home_lat'])
HOME_LNG = float(config['vehicle']['home_lng'])
EMAIL_1 = config['notification']['email_1']
buffer.close()

PCT_THRESHOLD = 0.5


##
# Set to run on an early morning cron job (before sunrise) that will 
# check today and tomorrow's weather and if more than a certain percentage 
# of rain is forecasted between sunrise and sunset, set the system to 
# backup mode so it will reserve the battery stored energy and prioritize 
# charging the battery in case there is an outage.  There tends not to be 
# enough solar generation during rainy days for self-powered or time-based
# control modes while also recharging the battery to 100%.  
#
# author: mjhwa@yahoo.com
##
def setEnergyModeBasedOnWeather():
  try:
    # get weather forecast
    wdata = getDailyWeather(HOME_LAT, HOME_LNG)
    check_dates = [date.today(), (date.today() + timedelta(1))]
    msg = ''

    for i, value in enumerate(check_dates):
      forecast = ''
      rain = 0
      total = 0

      # get sunrise and sunset times 
      for j, value in enumerate(wdata['daily']):
        dt = datetime.fromtimestamp(value['dt'])
        weather = value['weather'][0]['main']

        if ((dt.year == check_dates[i].year)
            and (dt.month == check_dates[i].month)
            and (dt.day == check_dates[i].day)):
          sunrise = datetime.fromtimestamp(value['sunrise'])
          sunset = datetime.fromtimestamp(value['sunset'])

      # loop through the hourly weather matching year, month, day, and 
      # between the hour values of sunrise and sunset
      for j, value in enumerate(wdata['hourly']):
        dt = datetime.fromtimestamp(value['dt'])

        if ((dt.year == check_dates[i].year)
            and (dt.month == check_dates[i].month)
            and (dt.day == check_dates[i].day)
            and (dt.hour >= sunrise.hour)
            and (dt.hour <= sunset.hour)):

          forecast += str(dt) + ': ' + value['weather'][0]['main'] + '\n'

          # count how many 'Rain' hours there are
          if (value['weather'][0]['main'] == 'Rain'):
            rain += 1

          # count how many total hours there are between sunrise and sunset
          total += 1

      # if the ratio of rain to non-rain hours is greater than a specified
      # percentage, set backup only mode, otherwise set time-based control mode
      if ((float(rain) / float(total)) > PCT_THRESHOLD): 
        setBatteryModeBackup()

        msg += 'Greater than ' + str(int(PCT_THRESHOLD * 100))
        msg += '% rain forecasted, setting backup only mode\n'
        msg += 'Percent rain: ' 
        msg += str(float(rain) / float(total) * 100) + '%\n'
        msg += forecast + '\n'
      else:
        # if none of the days is above the threshold
        if (msg == ''):
          setBatteryModeAdvancedCost()
          setBatteryBackupReserve(35)

    if (msg != ''):
      sendEmail(EMAIL_1, 
                'Energy:  Switching to Backup Only Mode', 
                msg, 
                '', 
                '')
  except Exception as e:
    logError('setEnergyModeBasedOnWeather(): ' + str(e))


def main():
  setEnergyModeBasedOnWeather()

if __name__ == "__main__":
  main()

