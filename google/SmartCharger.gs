var M3_VIN = crypto('0123456789');  
var MX_VIN = crypto('0123456789');  
var PRIMARY_LAT = parseFloat(crypto('20.123456789');  // get this from Google Maps
var PRIMARY_LNG = parseFloat(crypto('-100.12345689');  // get this from Google Maps
var SECONDARY_LAT = parseFloat(crypto('20.123456789');  // get this from Google Maps
var SECONDARY_LNG = parseFloat(crypto('-100.12345689');  // get this from Google Maps
var EV_SPREADSHEET_ID = crypto('abcdef0123456789');  // this can be a database
var EMAIL_ADDRESS_1 = crypto('email@email.com');
var EMAIL_ADDRESS_2 = crypto('email2@email.com');
var ACCESS_TOKEN = reuseAccessToken();

var WAIT_TIME = 30000;  // 30 seconds
var R = 3958.8;  // Earth radius in miles
var MX_FULL_CHARGE_RATE_AT_PRIMARY = 25;  // (mi/hr)
var M3_FULL_CHARGE_RATE_AT_PRIMARY = 37;  // (mi/hr)
var MX_FULL_CHARGE_RATE_AT_SECONDARY = 20;  // (mi/hr)
var M3_FULL_CHARGE_RATE_AT_SECONDARY = 30;  // (mi/hr)
var BASE_URL = 'https://owner-api.teslamotors.com/api/1/vehicles/';


/**
 * Checks to see if the vehicles are plugged in, inferred from the charge 
 * port door status, and sends an email to notify if it's not.  Also sets 
 * vehicles to start charging at the calculated date and time. Skips if 
 * it's not within 0.25 miles from your primary location.
 *
 * If one of the other cars is in a secondary location, set time charge 
 * start time based on the alternate charge rate and set the charge start time
 * for the one at the primary location to charge at full charge rate. 
 * 
 * author: mjhwa@yahoo.com
 */
function notifyIsTeslaPluggedIn() {
  try {
    // get all vehicle data to avoid repeat API calls
    var m3_data = getVehicleData(M3_VIN);
    var mx_data = getVehicleData(MX_VIN);
    
    // get car info
    var charge_port_door_open = m3_data.response.charge_state.charge_port_door_open;
    var battery_level = m3_data.response.charge_state.battery_level;
    var battery_range = m3_data.response.charge_state.battery_range;

    // get charging configuration info
    var charge_config = Sheets.Spreadsheets.Values.get(EV_SPREADSHEET_ID, 'Smart Charger!B3:B7').values
    
    // check if email notification is set to "on" first 
    if (charge_config[1][0] == 'on') {
      // send an email if the charge port door is not open, i.e. not plugged in
      if (!charge_port_door_open) {
        var message =  'Your car is not plugged in.  \n\nCurrent battery level is ' 
            message += battery_level + '%, ' 
            message += battery_range + ' estimated miles.  \n\n-Your Model 3';
        MailApp.sendEmail(EMAIL_ADDRESS_1, 'Please Plug In Your Model 3', message);
      } 
    }
    
    charge_port_door_open = mx_data.response.charge_state.charge_port_door_open;
    battery_level = mx_data.response.charge_state.battery_level;
    battery_range = mx_data.response.charge_state.battery_range;

    // check if email notification is set to "on" first 
    if (charge_config[0][0] == 'on') {
      // send an email if the charge port door is not open, i.e. not plugged in
      if (!charge_port_door_open) {
        message =  'Your car is not plugged in.  \n\nCurrent battery level is ' 
        message += battery_level + '%, ' 
        message += battery_range + ' estimated miles.  \n\n-Your Model X';
        MailApp.sendEmail(EMAIL_ADDRESS_2, 'Please Plug In Your Model X', message, {cc: EMAIL_ADDRESS_1});
      }
    }
    
    // set for scheduled charging 
    m3_target_finish_time = getTomorrowTime(charge_config[4][0]);
    mx_target_finish_time = getTomorrowTime(charge_config[3][0]);

    scheduleM3Charging(m3_data, mx_data, m3_target_finish_time, mx_target_finish_time);
    scheduleMXCharging(m3_data, mx_data, m3_target_finish_time, mx_target_finish_time);

    // get climate configuration info
    var climate_config = Sheets.Spreadsheets.Values.get(EV_SPREADSHEET_ID, 'Smart Climate!B20:I24').values;

    // set preconditioning the next morning
    setM3Precondition(m3_data, climate_config);
    setMXPrecondition(mx_data, climate_config);
  } catch (e) {
    logError('notifyIsTeslaPluggedIn(): ' + e);
    wakeVehicle(M3_VIN);
    wakeVehicle(MX_VIN);
    Utilities.sleep(WAIT_TIME);
    notifyIsTeslaPluggedIn();
  }
}


/**
 * Called by a trigger to read vehicle range and expected charge 
 * finish time from a Google Sheet, then call the API to set a time 
 * for scheduled charging in the vehicle.
 * 
 * author: mjhwa@yahoo.com
 */
function scheduleM3Charging(m3_data, mx_data, m3_target_finish_time, mx_target_finish_time) {
  if (m3_data.response.charge_state.charging_state != 'Complete') {  
    // get calculated start time depending on location of cars
    if (isVehicleAtPrimary(m3_data) && isVehicleAtPrimary(mx_data)) {
      var start_time = calculateScheduledCharging('m3_primary_shared_charging', 
                                                  m3_data,
                                                  mx_data,
                                                  m3_target_finish_time,
                                                  mx_target_finish_time)
    } else if (isVehicleAtPrimary(m3_data) && !isVehicleAtPrimary(mx_data)) {
      var start_time = calculateScheduledCharging('m3_primary_full_rate', 
                                                  m3_data,
                                                  mx_data,
                                                  m3_target_finish_time,
                                                  mx_target_finish_time)
    } else if (isVehicleAtSecondary(m3_data)) {
      var start_time = calculateScheduledCharging('m3_secondary_full_rate', 
                                                  m3_data,
                                                  mx_data,
                                                  m3_target_finish_time,
                                                  mx_target_finish_time)
    } else {
      return;
    }

    var total_minutes = (start_time.getHours() * 60) + start_time.getMinutes();
    
    setScheduledCharging(M3_VIN, total_minutes);
    stopChargeVehicle(M3_VIN);  // for some reason charging starts sometimes after scheduled charging API is called

    // send email notification
    var message = 'The Model 3 is set to charge at ' + start_time.toString() + '.';
    MailApp.sendEmail(EMAIL_ADDRESS_1, 'Model 3 Set to Charge', message);
  }
}


function scheduleMXCharging(m3_data, mx_data, m3_target_finish_time, mx_target_finish_time) {
  if (mx_data.response.charge_state.charging_state != 'Complete') {  
    // get calculated start time depending on location of cars
    if (isVehicleAtPrimary(mx_data) && isVehicleAtPrimary(m3_data)) {
      var start_time = calculateScheduledCharging('mx_primary_shared_charging', 
                                                  m3_data,
                                                  mx_data,
                                                  m3_target_finish_time,
                                                  mx_target_finish_time)
    } else if (isVehicleAtPrimary(mx_data) && !isVehicleAtPrimary(m3_data)) {
      var start_time = calculateScheduledCharging('mx_primary_full_rate', 
                                                  m3_data,
                                                  mx_data,
                                                  m3_target_finish_time,
                                                  mx_target_finish_time)
    } else if (isVehicleAtSecondary(mx_data)) {
      var start_time = calculateScheduledCharging('mx_secondary_full_rate', 
                                                  m3_data,
                                                  mx_data,
                                                  m3_target_finish_time,
                                                  mx_target_finish_time)
    } else {
      return;
    }

    var total_minutes = (start_time.getHours() * 60) + start_time.getMinutes();

    setScheduledCharging(MX_VIN, total_minutes);
    stopChargeVehicle(MX_VIN);  // for some reason charging starts sometimes after scheduled charging API is called
    
    // send email notification
    var message = 'The Model X is set to charge at ' + start_time.toString() + '.';
    MailApp.sendEmail(EMAIL_ADDRESS_1, 'Model X Set to Charge', message);
  }
}


/**
 * Add or subtract hours from a date object.
 *
 * author: mjhwa@yahoo.com
 */
function timeDelta(date, h) {
  return new Date(date.getTime() + h * (3600 * 1000));
}


/**
 * Helps format the charging or preconditioning time by defaulting the date.
 *
 * author: mjhwa@yahoo.com
 */
function getTomorrowTime(time) {
  var tomorrow_date = new Date(Date.now() + 1000 * 60 * 60 * 24).toLocaleDateString();    
  return new Date (tomorrow_date + ' ' + time);
}


/**
 * Calculates the scheduled charging time for 2 vehicles depending
 * on their location, charge state, and finish time.
 *
 * author: mjhwa@yahoo.com
 */
function calculateScheduledCharging(scenario, m3_data, mx_data, m3_target_finish_time, mx_target_finish_time) {
  try {
    // Calculate how many miles are needed for charging based on 
    // current range and charging % target
    var mx_current_range = mx_data['response']['charge_state']['battery_range'];
    var m3_current_range = m3_data['response']['charge_state']['battery_range'];

    var mx_max_range = (   mx_data['response']['charge_state']['battery_range'] 
                        / (mx_data['response']['charge_state']['battery_level'] / 100.0));
    var m3_max_range = (   m3_data['response']['charge_state']['battery_range'] 
                        / (m3_data['response']['charge_state']['battery_level'] / 100.0));

    var mx_charge_limit = mx_data['response']['charge_state']['charge_limit_soc'] / 100.0;
    var m3_charge_limit = m3_data['response']['charge_state']['charge_limit_soc'] / 100.0;

    var mx_target_range = mx_max_range * mx_charge_limit;
    var m3_target_range = m3_max_range * m3_charge_limit;

    var mx_miles_needed = 0;
    if ((mx_target_range - mx_current_range) > 0) { mx_miles_needed = mx_target_range - mx_current_range;}
    var m3_miles_needed = 0;
    if ((m3_target_range - m3_current_range) > 0) { m3_miles_needed = m3_target_range - m3_current_range;}

    // Calculate scheduled charging time based on location of cars
    if ((scenario == 'mx_primary_shared_charging') || (scenario == 'm3_primary_shared_charging')) {
      Logger.log('*shared charging');

      var mx_charging_time_at_full_rate = mx_miles_needed / MX_FULL_CHARGE_RATE_AT_PRIMARY;  // hours
      var m3_charging_time_at_full_rate = m3_miles_needed / M3_FULL_CHARGE_RATE_AT_PRIMARY;  // hours

      var mx_start_time_at_full_rate = timeDelta(mx_target_finish_time, -mx_charging_time_at_full_rate);
      var m3_start_time_at_full_rate = timeDelta(m3_target_finish_time, -m3_charging_time_at_full_rate);

      Logger.log('  mx full rate charging times: ' 
                 + Utilities.formatDate(mx_start_time_at_full_rate, 
                                        TIME_ZONE, 
                                        DATE_FORMAT) 
                 + ' to ' 
                 + Utilities.formatDate(mx_target_finish_time, 
                                        TIME_ZONE, 
                                        DATE_FORMAT) 
      );
      Logger.log('  m3 full rate charging times: ' 
                 + Utilities.formatDate(m3_start_time_at_full_rate, 
                                        TIME_ZONE, 
                                        DATE_FORMAT) 
                 + ' to ' 
                 + Utilities.formatDate(m3_target_finish_time, 
                                        TIME_ZONE, 
                                        DATE_FORMAT) 
      );

      // Determine if there is a charging time overlap
      var overlap = false;
      if((mx_start_time_at_full_rate.valueOf() < m3_target_finish_time.valueOf()) && 
         (m3_start_time_at_full_rate.valueOf() < mx_target_finish_time.valueOf()) &&
         (mx_start_time_at_full_rate.getTime() - mx_target_finish_time.getTime() != 0) &&
         (m3_start_time_at_full_rate.getTime() - m3_target_finish_time.getTime() != 0)) {
          overlap = true;
      }      
      // 1.  Charging times don't overlap
      //
      //                                     Charging at full rate   | 10:00
      // Car 1                           |===========================|
      // Car 2 |======================|
      //        Charging at full rate | 7:00
      if (overlap == false) {
        Logger.log('  no overlap');

        if (scenario == 'm3_primary_shared_charging') { 
          return m3_start_time_at_full_rate;
        }

        if (scenario == 'mx_primary_shared_charging') {
          return mx_start_time_at_full_rate;
        }
      } else {
      // 2a.  Charging times overlap, fully with different finish times
      //
      //       Charging at 
      //       full rate                        Charging at full rate | 10:00
      // Car 1 |============|==============|==========================|
      // Car 2              |==============|
      //             Charging at half rate | 7:00
        if (
             (mx_target_finish_time.valueOf() != m3_target_finish_time.valueOf()) && 
               (
                 (
                   (mx_start_time_at_full_rate.valueOf() < m3_start_time_at_full_rate.valueOf()) && 
                   (mx_target_finish_time.valueOf() > m3_target_finish_time.valueOf())
                 ) ||
                 (
                   (m3_start_time_at_full_rate.valueOf() < mx_start_time_at_full_rate.valueOf()) && 
                   (m3_target_finish_time.valueOf() > mx_target_finish_time.valueOf())
                 )
               )
           ) {
          Logger.log('  overlap, fully with different finish times');

          // Find the longer session
          if ((mx_target_finish_time.getTime() - mx_start_time_at_full_rate.getTime()) > 
              (m3_target_finish_time.getTime() - m3_start_time_at_full_rate.getTime())) {
            // Car 2
            var m3_charging_time_at_half_rate = m3_miles_needed / (M3_FULL_CHARGE_RATE_AT_PRIMARY / 2);
            var m3_start_time = timeDelta(m3_target_finish_time, -m3_charging_time_at_half_rate);

            // Car 1
            var mx_miles_added_at_full_rate = (mx_target_finish_time.getTime() - m3_target_finish_time.getTime())
                                               / 1000 / 60 / 60 * MX_FULL_CHARGE_RATE_AT_PRIMARY;
            var mx_miles_added_at_half_rate = m3_charging_time_at_half_rate 
                                              * (MX_FULL_CHARGE_RATE_AT_PRIMARY / 2);
            var mx_miles_remaining = mx_miles_needed 
                                     - mx_miles_added_at_full_rate 
                                     - mx_miles_added_at_half_rate;
            var mx_start_time = timeDelta(mx_target_finish_time, 
                                          -(mx_miles_added_at_full_rate / MX_FULL_CHARGE_RATE_AT_PRIMARY)
                                          -(mx_miles_added_at_half_rate / (MX_FULL_CHARGE_RATE_AT_PRIMARY / 2))
                                          -(mx_miles_remaining / MX_FULL_CHARGE_RATE_AT_PRIMARY)
                                         );

          } else {
            // Car 2
            var mx_charging_time_at_half_rate = mx_miles_needed / (MX_FULL_CHARGE_RATE_AT_PRIMARY / 2);
            var mx_start_time = timeDelta(mx_target_finish_time, -mx_charging_time_at_half_rate);

            // Car 1
            var m3_miles_added_at_full_rate = (m3_target_finish_time.getTime() - mx_target_finish_time.getTime())
                                               / 1000 / 60 / 60 * M3_FULL_CHARGE_RATE_AT_PRIMARY;
            var m3_miles_added_at_half_rate = mx_charging_time_at_half_rate 
                                              * (M3_FULL_CHARGE_RATE_AT_PRIMARY / 2);
            var m3_miles_remaining = m3_miles_needed 
                                     - m3_miles_added_at_full_rate 
                                     - m3_miles_added_at_half_rate;
            var m3_start_time = timeDelta(m3_target_finish_time, 
                                          -(m3_miles_added_at_full_rate / M3_FULL_CHARGE_RATE_AT_PRIMARY)
                                          -(m3_miles_added_at_half_rate / (M3_FULL_CHARGE_RATE_AT_PRIMARY / 2))
                                          -(m3_miles_remaining / M3_FULL_CHARGE_RATE_AT_PRIMARY)
                                         );
          }

      // 2b.  Charging times overlap, partially
      //
      //                                        Charging at full rate | 10:00
      // Car 1                      |=======|=========================|
      // Car 2 |====================|=======|
      //        Charging at full            | 7:00
      //        rate                Charging at 
      //                            half rate
        } else if (mx_target_finish_time.valueOf() > m3_target_finish_time.valueOf()) {
          Logger.log('  overlap, partially');

          // Car 1
          var mx_miles_added_at_full_rate = ((mx_target_finish_time.getTime() - m3_target_finish_time.getTime())
                                              / 1000 / 60 / 60 
                                              * MX_FULL_CHARGE_RATE_AT_PRIMARY);
          var mx_miles_remaining = mx_miles_needed - mx_miles_added_at_full_rate;
          var mx_charging_time_at_half_rate = mx_miles_remaining / (MX_FULL_CHARGE_RATE_AT_PRIMARY / 2);  // hours
          var mx_start_time = timeDelta(m3_target_finish_time, -mx_charging_time_at_half_rate);

          // Car 2
          var m3_miles_added_at_half_rate = ((m3_target_finish_time.getTime() - mx_start_time.getTime())
                                              / 1000 / 60 / 60 
                                              * (M3_FULL_CHARGE_RATE_AT_PRIMARY / 2));
          var m3_miles_remaining = m3_miles_needed - m3_miles_added_at_half_rate;
          var m3_charging_time_at_full_rate = m3_miles_remaining / M3_FULL_CHARGE_RATE_AT_PRIMARY;  // hours
          var m3_start_time = timeDelta(mx_start_time, -m3_charging_time_at_full_rate);

        } else if (mx_target_finish_time.valueOf() < m3_target_finish_time.valueOf()) {
          Logger.log('  overlap, partially');

          // Car 1
          var m3_miles_added_at_full_rate = ((m3_target_finish_time.getTime() - mx_target_finish_time.getTime())
                                              / 1000 / 60 / 60 
                                              * M3_FULL_CHARGE_RATE_AT_PRIMARY);
          var m3_miles_remaining = m3_miles_needed - m3_miles_added_at_full_rate;
          var m3_charging_time_at_half_rate = m3_miles_remaining / (M3_FULL_CHARGE_RATE_AT_PRIMARY / 2);  // hours
          var m3_start_time = timeDelta(mx_target_finish_time, -m3_charging_time_at_half_rate);

          // Car 2
          var mx_miles_added_at_half_rate = ((mx_target_finish_time.getTime() - m3_start_time.getTime())
                                              / 1000 / 60 / 60 
                                              * (MX_FULL_CHARGE_RATE_AT_PRIMARY / 2));
          var mx_miles_remaining = mx_miles_needed - mx_miles_added_at_half_rate;
          var mx_charging_time_at_full_rate = mx_miles_remaining / MX_FULL_CHARGE_RATE_AT_PRIMARY;  // hours
          var mx_start_time = timeDelta(m3_start_time, -mx_charging_time_at_full_rate);

      // 2c.  Charging times overlap, fully with the same finish times
      //          
      // For the longer/earlier start time, calculate the start time based on a part of 
      // the charging session being at half rate and another part at full rate.  The session 
      // will charge at half rate when the other car begins charging but the difference in 
      // miles/charge that starts before the other car will be at full rate.
      //
      //                                  Charging at half rate   | 07:00
      // Car 1                        |===========================|
      // Car 2 |======================|===========================|
      //        Charging at full rate 
        } else if (mx_target_finish_time.valueOf() == m3_target_finish_time.valueOf()) {
          Logger.log('  overlap, with the same finish times');

          var mx_charging_time_at_half_rate = mx_miles_needed / (MX_FULL_CHARGE_RATE_AT_PRIMARY / 2);  // hours
          var m3_charging_time_at_half_rate = m3_miles_needed / (M3_FULL_CHARGE_RATE_AT_PRIMARY / 2);  // hours

          var mx_start_time_at_half_rate = timeDelta(mx_target_finish_time, -mx_charging_time_at_half_rate);
          var m3_start_time_at_half_rate = timeDelta(m3_target_finish_time, -m3_charging_time_at_half_rate);

          if (mx_start_time_at_half_rate < m3_start_time_at_half_rate) {
            // Car 1 (The shorter/later start time will charge at half rate the entire session)
            var m3_start_time = m3_start_time_at_half_rate;

            // Car 2
            var mx_miles_added_at_half_rate = ((mx_target_finish_time.getTime() 
                                                - m3_start_time_at_half_rate.getTime()
                                               )/ 1000 / 60 / 60
                                                * (MX_FULL_CHARGE_RATE_AT_PRIMARY / 2));
            var mx_miles_remaining = mx_miles_needed - mx_miles_added_at_half_rate;
            var mx_miles_remaining_charging_time_at_full_rate = mx_miles_remaining 
                                                                / MX_FULL_CHARGE_RATE_AT_PRIMARY;
            var mx_start_time = timeDelta(m3_start_time_at_half_rate, 
                                          -mx_miles_remaining_charging_time_at_full_rate);
          } else {
            // Car 1 (The shorter/later start time will charge at half rate the entire session)
            var mx_start_time = mx_start_time_at_half_rate;

            // Car 2
            var m3_miles_added_at_half_rate = ((m3_target_finish_time.getTime() 
                                                - mx_start_time_at_half_rate.getTime()
                                               )/ 1000 / 60 / 60
                                                * (M3_FULL_CHARGE_RATE_AT_PRIMARY / 2));
            var m3_miles_remaining = m3_miles_needed - m3_miles_added_at_half_rate;
            var m3_miles_remaining_charging_time_at_full_rate = m3_miles_remaining 
                                                                / M3_FULL_CHARGE_RATE_AT_PRIMARY;
            var m3_start_time = timeDelta(mx_start_time_at_half_rate, 
                                          -m3_miles_remaining_charging_time_at_full_rate);
          }
        }

        if (scenario == 'm3_primary_shared_charging') {
          return m3_start_time;
        }

        if (scenario == 'mx_primary_shared_charging') {
          return mx_start_time;
        }
      }
    } else if (scenario == 'mx_primary_full_rate') {
      Logger.log('*mx at primary, m3 not at primary');

      mx_start_time = timeDelta(mx_target_finish_time, -(mx_miles_needed / MX_FULL_CHARGE_RATE_AT_PRIMARY));
      
      return mx_start_time;
    } else if (scenario == 'm3_primary_full_rate') {
      Logger.log('*m3 at primary, mx not at primary');

      m3_start_time = timeDelta(m3_target_finish_time, -(m3_miles_needed / M3_FULL_CHARGE_RATE_AT_PRIMARY));
      
      return m3_start_time;
    } else if (scenario == 'mx_secondary_full_rate') {
      Logger.log('*mx at secondary');

      mx_start_time = timeDelta(mx_target_finish_time, -(mx_miles_needed / MX_FULL_CHARGE_RATE_AT_SECONDARY));
      
      return mx_start_time;
    } else if (scenario == 'm3_secondary_full_rate') {
      Logger.log('*m3 at secondary');

      m3_start_time = timeDelta(m3_target_finish_time, -(m3_miles_needed / M3_FULL_CHARGE_RATE_AT_SECONDARY));

      return m3_start_time;
    }
  } catch(e) {
    logError('calculateScheduledCharging(' + scenario + '): ' + e)
  }
}


/**
 * Calculates if the distance of the car is greater than 0.25 miles 
 * away from a location.  The calculation uses Haversine Formula 
 * expressed in terms of a two-argument inverse tangent function to 
 * calculate the great circle distance between two points on the Earth. 
 * This is the method recommended for calculating short distances by 
 * Bob Chamberlain (rgc@jpl.nasa.gov) of Caltech and NASA's Jet 
 * Propulsion Laboratory as described on the U.S. Census Bureau web site.
 *
 * author: mjhwa@yahoo.com
 */
function isVehicleAtPrimary(data) {
  return isVehicleAtLocation(data, PRIMARY_LAT, PRIMARY_LNG);
}


function isVehicleAtSecondary(data) {
  return isVehicleAtLocation(data, SECONDARY_LAT, SECONDARY_LNG);
}


function isVehicleAtLocation(data, lat, lng) {
  var d = getDistance(data.response.drive_state.latitude, data.response.drive_state.longitude, lat, lng);
  
  // check if the car is more than a quarter of a mile away from a certain location
  if (d < 0.25) {
    return true;
  } else {
    return false;
  }
}


function getDistance(car_lat, car_lng, x_lat, x_lng) {
  var diff_lat = toRad(car_lat - x_lat);
  var diff_lng = toRad(car_lng - x_lng);  
  
  var a = (Math.sin(diff_lat/2) * Math.sin(diff_lat/2)) + Math.cos(x_lat) * Math.cos(car_lat) * (Math.sin(diff_lng/2) * Math.sin(diff_lng/2));
  var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  var d = R * c;
  
  return d;
}


function toRad(x) {
  return x * Math.PI / 180;
}


/**
 * Function to send API call to start charging a vehicle.
 * 
 * author: mjhwa@yahoo.com
 */
function chargeVehicle(vin) {
  try {
    var url = BASE_URL + getVehicleId(vin) + '/command/charge_start';
    var options = {
      'headers': {
        'authorization': 'Bearer ' + ACCESS_TOKEN
      },
      'method': 'post',
      'contentType': 'application/json'
    };
    var response = UrlFetchApp.fetch(url, options);
    return response;
  } catch (e) {
    logError('chargeVehicle(' + vin + '): ' + e);
    wakeVehicle(vin);
    Utilities.sleep(WAIT_TIME);
    chargeVehicle(vin);
  }
}


/**
 * Function to send API call to stop charging a vehicle.
 * 
 * author: mjhwa@yahoo.com
 */
function stopChargeVehicle(vin) {
  try {
    var url = BASE_URL + getVehicleId(vin) + '/command/charge_stop';
    var options = {
      'headers': {
        'authorization': 'Bearer ' + ACCESS_TOKEN
      },
      'method': 'post',
      'contentType': 'application/json'
    };
    var response = UrlFetchApp.fetch(url, options);
    return response;
  } catch (e) {
    logError('stopChargeVehicle(' + vin + '): ' + e);
    wakeVehicle(vin);
    Utilities.sleep(WAIT_TIME);
    stopChargeVehicle(vin);
  }
}


/**
 * Sends command and parameter to set a specific vehicle to charge
 * at a scheduled time.  Scheduled Time is in minutes, e.g. 7:30 AM =
 * (7 * 60) + 30 = 450
 *
 * author: mjhwa@yahoo.com
 */
function setScheduledCharging(vin, time) {
  try {
    var url = BASE_URL + getVehicleId(vin) + '/command/set_scheduled_charging';
    var data = {
      'enable': 'true',
      'time': time
    };

    var options = {
      'headers': {
        'authorization': 'Bearer ' + ACCESS_TOKEN
      },
      'method': 'post',
      'contentType': 'application/json',
      'payload': JSON.stringify(data)
    };
    var response = UrlFetchApp.fetch(url, options);
    return response;
  } catch (e) {
    logError('setScheduledCharging(' + vin + '): ' + e);
    wakeVehicle(vin);
    Utilities.sleep(WAIT_TIME);
    setScheduledCharging(vin, time);
  }
}


/**
 * Sends command and parameters to set a specific vehicle to charge and/or
 * precondition by a departure time.  Departure Time and Off-Peak Charge End 
 * Time are in minutes, e.g. 7:30 AM = (7 * 60) + 30 = 450
 * 
 * author: mjhwa@yahoo.com
 */
function setScheduledDeparture(
  vin, 
  depart_time, 
  precondition_enable, 
  precondition_weekdays, 
  off_peak_charging_enable, 
  off_peak_weekdays, 
  off_peak_end_time
) {
  try {
    var url = BASE_URL + getVehicleId(vin) + '/command/set_scheduled_departure';
    var data = {
      'enable': 'True',
      'departure_time': depart_time,
      'preconditioning_enabled': precondition_enable,
      'preconditioning_weekdays_only': precondition_weekdays,
      'off_peak_charging_enabled': off_peak_charging_enable,
      'off_peak_charging_weekdays_only': off_peak_weekdays,
      'end_off_peak_time': off_peak_end_time
    };

    var options = {
      'headers': {
        'authorization': 'Bearer ' + ACCESS_TOKEN
      },
      'method': 'post',
      'contentType': 'application/json',
      'payload': data
    };
    var response = UrlFetchApp.fetch(url, options);
    return response;
  } catch (e) {
    logError('setScheduledDeparture(' + vin + '): ' + e);
    wakeVehicle(vin);
    Utilities.sleep(WAIT_TIME);
    setScheduledDeparture(
      vin, 
      depart_time, 
      precondition_enable, 
      precondition_weekdays, 
      off_peak_charging_enable, 
      off_peak_weekdays, 
      off_peak_end_time
    );  
  }
}


/**
 * Sends command to set the charging amps for a specified vehicle.
 * 
 * author: mjhwa@yahoo.com
 */
function setChargingAmps(vin, amps) {
  try {
    var url = BASE_URL + getVehicleId(vin) + '/command/set_charging_amps';
    var data = {
      'charging_amps': amps
    };

    var options = {
      'headers': {
        'authorization': 'Bearer ' + ACCESS_TOKEN
      },
      'method': 'post',
      'contentType': 'application/json',
      'payload': data
    };
    var response = UrlFetchApp.fetch(url, options);
    return response;
  } catch (e) {
    logError('setChargingAmps(' + vin + '): ' + e);
    wakeVehicle(vin);
    Utilities.sleep(WAIT_TIME);
    setChargingAmps(vin, amps);  
  }
}


/**
 * Function to repeatedly run (after a certain wait time) to 
 * wake the vehicle up when it's asleep.  It will time out from 
 * the Google Apps Script trigger after 3 minutes if it doesn't 
 * wake up.
 * 
 * author: mjhwa@yahoo.com
 */
function wakeVehicle(vin) {
  try {
    var url = BASE_URL + getVehicleId(vin) + '/wake_up';
    var options = {
      'headers': {
        'authorization': 'Bearer ' + ACCESS_TOKEN
      },
      'method': 'post',
      'contentType': 'application/json'
    };
    
    return UrlFetchApp.fetch(url, options);
  } catch (e) {
    logError('wakeVehicle(' + vin + '): ' + e);
    Utilities.sleep(WAIT_TIME);    
    wakeVehicle(vin)
  }
}


/**
 * Retrieves the vehicle data needed for higher level functions 
 * to perform calculations and actions.
 * 
 * author: mjhwa@yahoo.com
 */
function getVehicleData(vin) {
  try {
    var url = BASE_URL + getVehicleId(vin) + '/vehicle_data';
    
    var options = {
      'headers': {
        'authorization': 'Bearer ' + ACCESS_TOKEN
      }
    };
    var response = JSON.parse(UrlFetchApp.fetch(url, options).getContentText());

    if (vin == M3_VIN) {
      response = addVehicleLocationData(M3_VIN, response);
    }

    return response;
  } catch (e) {
    logError('getVehicleData(' + vin + '): ' + e);
  }
}

/**
 * Adds the vehicle latitude and longitude data from a separate API call
 * to an existing JSON object to account for recent return value changes 
 * for data privacy.
 * 
 * author: mjhwa@yahoo.com
 */
function addVehicleLocationData(vin, data) {
  var url = BASE_URL + getVehicleId(vin) + '/vehicle_data?endpoints=location_data';
  
  var options = {
    'headers': {
      'authorization': 'Bearer ' + ACCESS_TOKEN
    }
  };
  var response = JSON.parse(UrlFetchApp.fetch(url, options).getContentText());

  data['response']['drive_state']['latitude'] = response.response.drive_state.latitude;
  data['response']['drive_state']['longitude'] = response.response.drive_state.longitude;

  return data;
}


/**
 * Retrieves the vehicle ID, which changes from time to time, 
 * by the VIN, which doesn't change.  The vehicle ID is required 
 * for many of the API calls.
 * 
 * author: mjhwa@yahoo.com
 */
function getVehicleId(vin) {
  try {
    var url = BASE_URL;
    
    var options = {
      'headers': {
        'authorization': 'Bearer ' + ACCESS_TOKEN
      }
    };
    var response = JSON.parse(UrlFetchApp.fetch(url, options).getContentText());
    for (var x = 0; x < response.response.length; x++) {
      if (response.response[x].vin == vin) {
        return response.response[x].id_s;
      }
    }
  } catch (e) {
    logError('getVehicleId(' + vin + '): ' + e);
  }
}


/**
 * Lists out all vehicles and its data associated with an account.
 * 
 * author: mjhwa@yahoo.com
 */
function getVehicles() {
  try {
    var url = BASE_URL;
    
    var options = {
      'headers': {
        'authorization': 'Bearer ' + ACCESS_TOKEN
      }
    };
    var response = UrlFetchApp.fetch(url, options);
    Logger.log('Response: ' + response);
  } catch (e) {
    logError('getVehicles(): ' + e);
  }
}


/**
 * Loads access token generated by a seperate Python script.
 * This is easier to do in Python and copy over to Google Drive
 * because the access tokens expire more frequently (8 hours vs. 
 * than 45 days previously).  
 * 
 * author: mjhwa@yahoo.com
 */
function reuseAccessToken() {
  var file = DriveApp.getFilesByName('token.ini');
  var text;
  while (file.hasNext()) {
    text = file.next().getAs('application/octet-stream').getDataAsString().trim();
//    Logger.log('token: ' + text);
  }

  var decoded = decode(text);
//  Logger.log('decoded token: ' + decoded);

  return decoded;
}


/**
 * Basic encryption with a key file to avoid storing sensitive data in 
 * clear text.
 * 
 * author: mjhwa@yahoo.com
 */
function crypto(str) {
  var file = DriveApp.getFilesByName('key');
  var key;
  while (file.hasNext()) {
    key = file.next().getAs('application/octet-stream').getDataAsString();
  }

  var encoded = '';
  for (var i = 0; i < str.length; i++) {
      var a = str.charCodeAt(i);
      var b = a ^ key;    // bitwise XOR with any number, e.g. 123
      encoded = encoded + String.fromCharCode(b); 
  }

  return encoded;
}


/**
 * Decode a file using Base64 to make it easier to share
 * between Google Apps Script and Python, while not having
 * access tokens available in clear text.
 * 
 * author: mjhwa@yahoo.com
 */
function decode(str) {
  var decoded = Utilities.base64Decode(str);

  return Utilities.newBlob(decoded).getDataAsString().trim();
}
