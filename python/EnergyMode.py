import configparser
import os

from datetime import datetime, date, timedelta
from Utilities import getDailyWeather
from TeslaEnergyAPI import setBatteryModeBackup, setBatteryModeSelfPowered, setBatteryBackupReserve
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
buffer.close()

PCT_THRESHOLD = 0.5


##
# Set to run on an early morning cron job (before sunrise) that will 
# check tommorrow's weather and if more than a certain percentage of rain 
# is forecasted between sunrise and sunset, set the system to backup mode 
# so it will reserve the battery stored energy and prioritize charging the 
# battery in case there is an outage.  There tends not to be enough solar 
# generation during rainy days for self-powered mode and recharge the 
# battery to 100%.  
#
# author: mjhwa@yahoo.com
##
def setEnergyModeBasedOnWeather():
  try:
    # get weather forecast
    wdata = getDailyWeather(HOME_LAT, HOME_LNG)
    tomorrow = date.today() + timedelta(1)
#    print(tomorrow)
    rain = 0
    total = 0

    # get sunrise and sunset times for tomorrow
    for i, value in enumerate(wdata['daily']):
      dt = datetime.fromtimestamp(value['dt'])
      weather = value['weather'][0]['main']

#      print(str(dt) + ': ' + weather)

      if ((dt.year == tomorrow.year)
          and (dt.month == tomorrow.month)
          and (dt.day == tomorrow.day)):
        sunrise = datetime.fromtimestamp(value['sunrise'])
        sunset = datetime.fromtimestamp(value['sunset'])

#        print('sunrise: ' + str(sunrise))
#        print('sunset: ' + str(sunset))

    # loop through the hourly weather matching year, month, day, and 
    # between the hour values of sunrise and sunset
    for i, value in enumerate(wdata['hourly']):
      dt = datetime.fromtimestamp(value['dt'])

      if ((dt.year == tomorrow.year)
          and (dt.month == tomorrow.month)
          and (dt.day == tomorrow.day)
          and (dt.hour >= sunrise.hour)
          and (dt.hour <= sunset.hour)):

        print(str(dt) + ': ' + value['weather'][0]['main'])

        # count how many 'Rain' hours there are
        if (value['weather'][0]['main'] == 'Rain'):
          rain += 1

        # count how many total hours there are between sunrise and sunset
        total += 1

#    print(rain)
#    print(total)
#    print(float(rain) / float(total))

    # if the ratio of rain to non-rain hours is greater than a specified
    # percentage, set backup only mode, otherwise set self-powered mode
    if ((float(rain) / float(total)) > PCT_THRESHOLD): 
      print('Greater than ' 
            + str(int(PCT_THRESHOLD * 100))
            + '% rain forecasted, setting backup only mode')
      setBatteryModeBackup()
    else:
      print('Less than ' 
            + str(int(PCT_THRESHOLD * 100))
            + '% rain forecasted, setting self-powered mode')
      setBatteryModeSelfPowered()
      setBatteryBackupReserve(35)
  except Exception as e:
    logError('setEnergyModeBasedOnWeather(): ' + str(e))


def main():
  setEnergyModeBasedOnWeather()

if __name__ == "__main__":
  main()

