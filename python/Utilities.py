import math

from crontab import CronTab

R = 3958.8;  #Earth radius in miles
HOME_LAT = 
HOME_LNG = 
NAPA_LAT = 
NAPA_LNG = 

##
#
#
#
##
def deleteCronTab(command):
  cron = CronTab(user='pi')
  job = cron.find_command(command)
  cron.remove(job)
  cron.write()

##
#
#
#
##
def createCronTab(command, hour, minute):
  cron = CronTab(user='pi')
  job = cron.new(command=command)
  job.hour.on(hour)
  job.minute.on(minute)
  cron.write()

##
# Calculates if the distance of the car is greater than 0.25 miles away from
# home.  The calculation uses Haversine Formula expressed in terms of a
# two-argument inverse tangent function to calculate the great circle distance
# between two points on the Earth. This is the method recommended for
# calculating short distances by Bob Chamberlain (rgc@jpl.nasa.gov) of Caltech
# and NASA's Jet Propulsion Laboratory as described on the U.S. Census Bureau
# Web site.
#
# author: mjhwa@yahoo.com
##
def isVehicleAtHome(data):
  return isVehicleAtLocation(data, HOME_LAT, HOME_LNG)

def isVehicleAtNapa(data):
  return isVehicleAtLocation(data, NAPA_LAT, NAPA_LNG)

def isVehicleAtLocation(data, lat, lng):
  d = getDistance(data['response']['drive_state']['latitude'], data['response']['drive_state']['longitude'], lat, lng)

  # check if the car is more than a quarter of a mile away
  if (d < 0.25):
    return True
  else:
    return False

def getDistance(car_lat, car_lng, x_lat, x_lng):
  diff_lat = toRad(car_lat - x_lat)
  diff_lng = toRad(car_lng - x_lng)

  a = (math.sin(diff_lat/2) * math.sin(diff_lat/2)) + math.cos(x_lat) * math.cos(car_lat) * (math.sin(diff_lng/2) * math.sin(diff_lng/2))
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
  d = R * c

  return d

def toRad(x):
  return x * math.pi / 180
