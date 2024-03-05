from TeslaEnergyAPI import setBackupReserve
from Email import sendEmail
from Utilities import getDailyWeather, getConfig
from Logger import logError
from datetime import datetime, date, timedelta

config = getConfig()
PRIMARY_LAT = float(config['vehicle']['primary_lat'])
PRIMARY_LNG = float(config['vehicle']['primary_lng'])
EMAIL_1 = config['notification']['email_1']

PCT_THRESHOLD = 0.5


##
# Set to run on an early morning cron job (before sunrise) that will 
# check today and tomorrow's weather and if more than a certain percentage 
# of rain is forecasted between sunrise and sunset, set the backup reserve 
# to 100% so it will reserve the battery stored energy and prioritize 
# charging the battery in case there is an outage.  There tends not to be 
# enough solar generation during rainy days for self-powered or time-based
# control modes while also recharging the battery to 100%.  
#
# author: mjhwa@yahoo.com
##
def setEnergyModeBasedOnWeather():
  try:
    # get weather forecast
    wdata = getDailyWeather(PRIMARY_LAT, PRIMARY_LNG)
    check_dates = [date.today(), (date.today() + timedelta(1))]
    msg = ''

    for _, val_1 in enumerate(check_dates):
      forecast = ''
      rain = 0
      total = 0

      # get sunrise and sunset times 
      for _, val_2 in enumerate(wdata['daily']):
        dt = datetime.fromtimestamp(val_2['dt'])

        if ((dt.year == val_1.year)
            and (dt.month == val_1.month)
            and (dt.day == val_1.day)):
          sunrise = datetime.fromtimestamp(val_2['sunrise'])
          sunset = datetime.fromtimestamp(val_2['sunset'])

          # loop through the hourly weather matching year, month, day, and 
          # between the hour values of sunrise and sunset
          for _, val_3 in enumerate(wdata['hourly']):
            dt = datetime.fromtimestamp(val_3['dt'])

            if ((dt.year == val_1.year)
                and (dt.month == val_1.month)
                and (dt.day == val_1.day)
                and (dt.hour >= sunrise.hour)
                and (dt.hour <= sunset.hour)):
              weather = val_3['weather'][0]['main']
              forecast += str(dt) + ': ' + weather + '\n'

              # count how many 'Rain' hours there are
              if (weather == 'Rain'):
                rain += 1

              # count how many total hours there are between sunrise and sunset
              total += 1

				  # if the ratio of rain to non-rain hours is greater than a specified
				  # percentage, prep content for email
          if ((float(rain) / float(total)) > PCT_THRESHOLD): 
            msg += 'Greater than ' + str(int(PCT_THRESHOLD * 100))
            msg += '% rain forecasted, setting backup reserve to 100%\n'
            msg += 'Percent rain: ' 
            msg += str(round(float(rain) / float(total) * 100, 1)) + '%\n'
            msg += forecast + '\n'

	  # if the ratio of rain to non-rain hours for today or tomorrow
	  # is greater than a specified percentage, set backup reserve to
	  # 100% and send email, otherwise set to normal backup reserve of 35%
    if (msg != ''):
      setBackupReserve(100)
      sendEmail(EMAIL_1, 
                'Energy:  Setting Backup Reserve to 100%', 
                msg, 
                '', 
                '')
    else:
      setBackupReserve(35)
  except Exception as e:
    logError('setEnergyModeBasedOnWeather(): ' + str(e))


def main():
  setEnergyModeBasedOnWeather()

if __name__ == "__main__":
  main()

