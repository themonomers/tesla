var OPENWEATHERMAP_KEY = crypto('abcdef0123456789');


/**
 * Creates a trigger to precondition the cabin for the 
 * following morning, based on if the car is at the primary 
 * location and if "Eco Mode" is off similar to how Nest 
 * thermostats work for vacation scenarios.  With the new 
 * endpoints released, you can achieve the same functionality 
 * by setting scheduled departure for preconditioning.  I decided 
 * to keep this code as I don't drive long distances so the added 
 * feature of preconditioning the battery, in addition to the cabin, 
 * is a waste of energy (entropy) for me.
 *
 * author: mjhwa@yahoo.com
 */
function setM3Precondition(data, climate_config) {
  var tomorrow_date = new Date(Date.now() + 1000*60*60*24).toLocaleDateString();
  var eco_mode = climate_config[4][0];
    
  // check if eco mode is off and the car is with 0.25 miles of primary location
  if ((eco_mode == 'off') && (isVehicleAtPrimary(data))) {      
    // get start time preferences
    var start_time = climate_config[0][0];
      
    // specific date/time to create a trigger for tomorrow morning at the preferred start time
    var estimated_start_time = new Date (tomorrow_date + ' ' + start_time);
      
    // create precondition start trigger
    if (doesTriggerExist('preconditionM3Start')) { deleteTrigger('preconditionM3Start'); }
    ScriptApp.newTrigger('preconditionM3Start').timeBased().at(estimated_start_time).create();
  }
}


function setMXPrecondition(data, climate_config) {
  var tomorrow_date = new Date(Date.now() + 1000*60*60*24).toLocaleDateString();
  var eco_mode = climate_config[4][7];
  
  // check if eco mode is off and the car is with 0.25 miles of primary location
  if ((eco_mode == 'off') && (isVehicleAtPrimary(data))) { 
    // get start time preferences
    var start_time = climate_config[0][7];
      
    // specific date/time to create a trigger for tomorrow morning at the preferred start time
    var estimated_start_time = new Date (tomorrow_date + ' ' + start_time);
      
    // create precondition start trigger
    if (doesTriggerExist('preconditionMXStart')) { deleteTrigger('preconditionMXStart'); }
    ScriptApp.newTrigger('preconditionMXStart').timeBased().at(estimated_start_time).create();
  }
}


/**
 * Checks a Google Sheet for heating and cooling preferences 
 * and sends a command to precondition the car.  Includes seat 
 * heating preferences. Originally this just used the inside car 
 * temp but to also account for the outside temperature, it might 
 * be more comfortable for the occupants to look at the average 
 * of the two to determine when to pre-heat/cool.
 *
 * Currently using a weather API instead of the inside or outside 
 * temp data from the cars.  The temp data from the cars don't seem 
 * to be accurate enough and not representative of passenger comfort 
 * of when to pre-heat/cool.
 *
 * author: mjhwa@yahoo.com
 */
function preconditionM3Start() {
  try {    
    // get configuration info
    var climate_config = Sheets.Spreadsheets.Values.get(EV_SPREADSHEET_ID, 'Smart Climate!B3:H24').values;

    // check if eco mode is off first so we don't have to even call the Tesla API if we don't have to
    if (climate_config[21][0] == 'on') { return; }
    
    // get local weather
    var wdata = JSON.parse(getCurrentWeather(crypto('90210')).getContentText());
    
    // get data
    var cold_temp_threshold = Number(climate_config[19][0]);
    var hot_temp_threshold = Number(climate_config[20][0]);
      
    // get today's day of week to compare against Google Sheet temp preferences for that day
    var day_of_week = new Date().getDay();
    var d_temp;
    var p_temp;
    var seats = [];
    
    // compare temp readings and threshold to determine heating or cooling temps to use
    if (wdata.main.temp < cold_temp_threshold) {
      // get pre-heat preferences  
      if (day_of_week == 0) {  // Sunday
        d_temp = Number(climate_config[6][0]);
        p_temp = Number(climate_config[6][1]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(climate_config[6][2]));
        seats.push(Number(climate_config[6][3]));
        seats.push(Number(climate_config[6][4]));
        seats.push(-1); // placeholder for index 3 as it's not assigned in the API
        seats.push(Number(climate_config[6][5]));
        seats.push(Number(climate_config[6][6]));
      } else if (day_of_week == 1) {  // Monday
        d_temp = Number(climate_config[0][0]);
        p_temp = Number(climate_config[0][1]);  
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(climate_config[0][2]));
        seats.push(Number(climate_config[0][3]));
        seats.push(Number(climate_config[0][4]));
        seats.push(-1); // placeholder for index 3 as it's not assigned in the API
        seats.push(Number(climate_config[0][5]));
        seats.push(Number(climate_config[0][6]));
      } else if (day_of_week == 2) {  // Tuesday
        d_temp = Number(climate_config[1][0]);
        p_temp = Number(climate_config[1][1]);   
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }

        seats.push(Number(climate_config[1][2]));
        seats.push(Number(climate_config[1][3]));
        seats.push(Number(climate_config[1][4]));
        seats.push(-1); // placeholder for index 3 as it's not assigned in the API
        seats.push(Number(climate_config[1][5]));
        seats.push(Number(climate_config[1][6]));
      } else if (day_of_week == 3) {  // Wednesday
        d_temp = Number(climate_config[2][0]);
        p_temp = Number(climate_config[2][1]);   
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }

        seats.push(Number(climate_config[2][2]));
        seats.push(Number(climate_config[2][3]));
        seats.push(Number(climate_config[2][4]));
        seats.push(-1); // placeholder for index 3 as it's not assigned in the API
        seats.push(Number(climate_config[2][5]));
        seats.push(Number(climate_config[2][6]));
      } else if (day_of_week == 4) {  // Thursday
        d_temp = Number(climate_config[3][0]);
        p_temp = Number(climate_config[3][1]);  
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }

        seats.push(Number(climate_config[3][2]));
        seats.push(Number(climate_config[3][3]));
        seats.push(Number(climate_config[3][4]));
        seats.push(-1); // placeholder for index 3 as it's not assigned in the API
        seats.push(Number(climate_config[3][5]));
        seats.push(Number(climate_config[3][6]));
      } else if (day_of_week == 5) {  // Friday
        d_temp = Number(climate_config[4][0]);
        p_temp = Number(climate_config[4][1]);  
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }

        seats.push(Number(climate_config[4][2]));
        seats.push(Number(climate_config[4][3]));
        seats.push(Number(climate_config[4][4]));
        seats.push(-1); // placeholder for index 3 as it's not assigned in the API
        seats.push(Number(climate_config[4][5]));
        seats.push(Number(climate_config[4][6]));
      } else if (day_of_week == 6) {  // Saturday
        d_temp = Number(climate_config[5][0]);
        p_temp = Number(climate_config[5][1]);  
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }

        seats.push(Number(climate_config[5][2]));
        seats.push(Number(climate_config[5][3]));
        seats.push(Number(climate_config[5][4]));
        seats.push(-1); // placeholder for index 3 as it's not assigned in the API
        seats.push(Number(climate_config[5][5]));
        seats.push(Number(climate_config[5][6]));
      } else {
        return;
      }
    } else if (wdata.main.temp > hot_temp_threshold) {
      // get pre-cool preferences
      if (day_of_week == 0) {  // Sunday
        d_temp = Number(climate_config[15][0]);
        p_temp = Number(climate_config[15][1]);  
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }

        seats.push(Number(climate_config[15][2]));
        seats.push(Number(climate_config[15][3]));
        seats.push(Number(climate_config[15][4]));
        seats.push(-1); // placeholder for index 3 as it's not assigned in the API
        seats.push(Number(climate_config[15][5]));
        seats.push(Number(climate_config[15][6]));
      } else if (day_of_week == 1) {  // Monday
        d_temp = Number(climate_config[9][0]);
        p_temp = Number(climate_config[9][1]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(climate_config[9][2]));
        seats.push(Number(climate_config[9][3]));
        seats.push(Number(climate_config[9][4]));
        seats.push(-1); // placeholder for index 3 as it's not assigned in the API
        seats.push(Number(climate_config[9][5]));
        seats.push(Number(climate_config[9][6]));
      } else if (day_of_week == 2) {  // Tuesday
        d_temp = Number(climate_config[10][0]);
        p_temp = Number(climate_config[10][1]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(climate_config[10][2]));
        seats.push(Number(climate_config[10][3]));
        seats.push(Number(climate_config[10][4]));
        seats.push(-1); // placeholder for index 3 as it's not assigned in the API
        seats.push(Number(climate_config[10][5]));
        seats.push(Number(climate_config[10][6]));
      } else if (day_of_week == 3) {  // Wednesday
        d_temp = Number(climate_config[11][0]);
        p_temp = Number(climate_config[11][1]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(climate_config[11][2]));
        seats.push(Number(climate_config[11][3]));
        seats.push(Number(climate_config[11][4]));
        seats.push(-1); // placeholder for index 3 as it's not assigned in the API
        seats.push(Number(climate_config[11][5]));
        seats.push(Number(climate_config[11][6]));
      } else if (day_of_week == 4) {  // Thursday
        d_temp = Number(climate_config[12][0]);
        p_temp = Number(climate_config[12][1]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(climate_config[12][2]));
        seats.push(Number(climate_config[12][3]));
        seats.push(Number(climate_config[12][4]));
        seats.push(-1); // placeholder for index 3 as it's not assigned in the API
        seats.push(Number(climate_config[12][5]));
        seats.push(Number(climate_config[12][6]));
      } else if (day_of_week == 5) {  // Friday
        d_temp = Number(climate_config[13][0]);
        p_temp = Number(climate_config[13][1]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(climate_config[13][2]));
        seats.push(Number(climate_config[13][3]));
        seats.push(Number(climate_config[13][4]));
        seats.push(-1); // placeholder for index 3 as it's not assigned in the API
        seats.push(Number(climate_config[13][5]));
        seats.push(Number(climate_config[13][6]));
      } else if (day_of_week == 6) {  // Saturday
        d_temp = Number(climate_config[14][0]);
        p_temp = Number(climate_config[14][1]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(climate_config[14][2]));
        seats.push(Number(climate_config[14][3]));
        seats.push(Number(climate_config[14][4]));
        seats.push(-1); // placeholder for index 3 as it's not assigned in the API
        seats.push(Number(climate_config[14][5]));
        seats.push(Number(climate_config[14][6]));
      } else {
        return;
      }
    } else {
      return; // outside temp is within cold and hot thresholds so no preconditioning required; inside and outside car temp readings seem to be inaccurate until the HVAC runs
    }
  
    // no need to execute if unsure where the car is or if it's in motion
    var data = JSON.parse(getVehicleData(M3_VIN).getContentText());
    if (isVehicleAtPrimary(data)) {
      // send command to start auto conditioning
      preconditionCarStart(M3_VIN);  

      // set driver and passenger temps
      setCarTemp(M3_VIN, d_temp, p_temp);
      
      // set seat heater settings
      for (var i = 0; i < seats.length; i++) {
        if (i == 3) { i++; } // skip index 3 as it's not assigned in the API
        setCarSeatHeating(M3_VIN, i, seats[i]);
      }
      
      // get stop time preferences
      var stop_time = climate_config[18][0];
      
      // specific date/time to create a trigger at the preferred stop time (this doesn't seem to work outside of AM, might need refactoring)
      var estimated_stop_time = new Date (new Date().toLocaleDateString() + ' ' + stop_time);
      
      // create trigger to stop preconditioning
      if (!doesTriggerExist('preconditionM3Stop')) { ScriptApp.newTrigger('preconditionM3Stop').timeBased().at(estimated_stop_time).create(); }
    }
  } catch (e) {
    logError('preconditionM3Start(): ' + e);
    wakeVehicle(M3_VIN);
    Utilities.sleep(WAIT_TIME);
    preconditionM3Start();
  }
}


function preconditionMXStart() {
  try {
    // get configuration info
    var climate_config = Sheets.Spreadsheets.Values.get(EV_SPREADSHEET_ID, 'Smart Climate!I3:L24').values;

    // check if eco mode is off first so we don't have to even call the Tesla API if we don't have to
    if (climate_config[21][0] == 'on') { return; }
    
    // get local weather
    var wdata = JSON.parse(getCurrentWeather(crypto('90210')).getContentText());
    
    // get data
    var cold_temp_threshold = Number(climate_config[19][0]);
    var hot_temp_threshold = Number(climate_config[20][0]);

    // get today's day of week to compare against Google Sheet temp preferences for that day
    var day_of_week = new Date().getDay();
    var d_temp;
    var p_temp;
    var seats = [];
    
//    Logger.log('local weather: ' + data.main.temp);
    
    // compare temp readings and threshold to determine heating or cooling temps to use
    if (wdata.main.temp < cold_temp_threshold) {
      // get pre-heat preferences
      if (day_of_week == 0) {  // Sunday
        d_temp = Number(climate_config[6][0]);
        p_temp = Number(climate_config[6][1]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(climate_config[6][2]));
        seats.push(Number(climate_config[6][3]));
      } else if (day_of_week == 1) {  // Monday
        d_temp = Number(climate_config[0][0]);
        p_temp = Number(climate_config[0][1]);  
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(climate_config[0][2]));
        seats.push(Number(climate_config[0][3]));
      } else if (day_of_week == 2) {  // Tuesday
        d_temp = Number(climate_config[1][0]);
        p_temp = Number(climate_config[1][1]);   
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(climate_config[1][2]));
        seats.push(Number(climate_config[1][3]));
      } else if (day_of_week == 3) {  // Wednesday
        d_temp = Number(climate_config[2][0]);
        p_temp = Number(climate_config[2][1]);   
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(climate_config[2][2]));
        seats.push(Number(climate_config[2][3]));
      } else if (day_of_week == 4) {  // Thursday
        d_temp = Number(climate_config[3][0]);
        p_temp = Number(climate_config[3][1]);  
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(climate_config[3][2]));
        seats.push(Number(climate_config[3][3]));
      } else if (day_of_week == 5) {  // Friday
        d_temp = Number(climate_config[4][0]);
        p_temp = Number(climate_config[4][1]); 
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(climate_config[4][2]));
        seats.push(Number(climate_config[4][3]));
      } else if (day_of_week == 6) {  // Saturday
        d_temp = Number(climate_config[5][0]);
        p_temp = Number(climate_config[5][1]);  
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(climate_config[5][2]));
        seats.push(Number(climate_config[5][3]));
      } else {
        return;
      }
    } else if (wdata.main.temp > hot_temp_threshold) {
      // get pre-cool preferences
      if (day_of_week == 0) {  // Sunday
        d_temp = Number(climate_config[15][0]);
        p_temp = Number(climate_config[15][1]);  
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(climate_config[15][2]));
        seats.push(Number(climate_config[15][3]));
      } else if (day_of_week == 1) {  // Monday
        d_temp = Number(climate_config[9][0]);
        p_temp = Number(climate_config[9][1]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(climate_config[9][2]));
        seats.push(Number(climate_config[9][3]));
      } else if (day_of_week == 2) {  // Tuesday
        d_temp = Number(climate_config[10][0]);
        p_temp = Number(climate_config[10][1]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(climate_config[10][2]));
        seats.push(Number(climate_config[10][3]));
      } else if (day_of_week == 3) {  // Wednesday
        d_temp = Number(climate_config[11][0]);
        p_temp = Number(climate_config[11][1]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(climate_config[11][2]));
        seats.push(Number(climate_config[11][3]));
      } else if (day_of_week == 4) {  // Thursday
        d_temp = Number(climate_config[12][0]);
        p_temp = Number(climate_config[12][1]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(climate_config[12][2]));
        seats.push(Number(climate_config[12][3]));
      } else if (day_of_week == 5) {  // Friday
        d_temp = Number(climate_config[13][0]);
        p_temp = Number(climate_config[13][1]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(climate_config[13][2]));
        seats.push(Number(climate_config[13][3]));
      } else if (day_of_week == 6) {  // Saturday
        d_temp = Number(climate_config[14][0]);
        p_temp = Number(climate_config[14][1]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(climate_config[14][2]));
        seats.push(Number(climate_config[14][3]));
      } else {
        return;
      }
    } else {
      return; // outside temp is within cold and hot thresholds so no preconditioning required; inside and outside car temp readings seem to be inaccurate until the HVAC runs
    }

    // no need to execute if unsure where the car is or if it's in motion
    var data = JSON.parse(getVehicleData(MX_VIN).getContentText());
    if (isVehicleAtPrimary(data)) {
      // set driver and passenger temps
      setCarTemp(MX_VIN, d_temp, p_temp);
      
      // send command to start auto conditioning
      preconditionCarStart(MX_VIN);  
      
      // set seat heater settings
      for (var i = 0; i < seats.length; i++) {
        setCarSeatHeating(MX_VIN, i, seats[i]);
      }
      
      // get stop time preferences
      var stop_time = climate_config[18][0];
      
      // specific date/time to create a trigger at the preferred stop time (this doesn't seem to work outside of AM, might need refactoring)
      var estimated_stop_time = new Date (new Date().toLocaleDateString() + ' ' + stop_time);
      
      // create trigger to stop preconditioning
      if (!doesTriggerExist('preconditionMXStop')) { ScriptApp.newTrigger('preconditionMXStop').timeBased().at(estimated_stop_time).create(); }
    }
  } catch (e) {
    logError('preconditionMXStart(): ' + e);
    wakeVehicle(MX_VIN);
    Utilities.sleep(WAIT_TIME);
    preconditionMXStart();
  }
}


/**
 * Function to check if the car is at home before stopping
 * the HVAC.  This is so it doesn't change the HVAC state
 * while someone is driving the car.
 * 
 * author: mjhwa@yahoo.com
 */
function preconditionM3Stop() {
  try {
    var data = JSON.parse(getVehicleData(M3_VIN).getContentText());
    if (isVehicleAtPrimary(data) &&
         (data.response.drive_state.shift_state == 'P' ||
          data.response.drive_state.shift_state == 'None')) { // only execute if the car is at primary location and in park
      preconditionCarStop(M3_VIN);
    }
  } catch (e) {
    logError('preconditionM3Stop(): ' + e);
    wakeVehicle(M3_VIN);
    Utilities.sleep(WAIT_TIME);
    preconditionM3Stop();
  }
}


function preconditionMXStop() {
  try {
    var data = JSON.parse(getVehicleData(MX_VIN).getContentText());
    if (isVehicleAtPrimary(data) &&
         (data.response.drive_state.shift_state == 'P' ||
          data.response.drive_state.shift_state == 'None')) { // only execute if the car is at primary location and in park
      preconditionCarStop(MX_VIN);
    }
  } catch (e) {
    logError('preconditionMXStop(): ' + e);
    wakeVehicle(MX_VIN);
    Utilities.sleep(WAIT_TIME);
    preconditionMXStop();
  }
}


/**
 * Function to send API call to set driver and passenger
 * temperature.
 * 
 * author: mjhwa@yahoo.com
 */
function setCarTemp(vin, d_temp, p_temp) {
  var url = BASE_URL + getVehicleId(vin) + '/command/set_temps';
  var options = {
    "headers": {
      "authorization": "Bearer " + ACCESS_TOKEN
    },
    "method": "post",
    "contentType": "application/json",
    "payload": JSON.stringify({'driver_temp': d_temp, 'passenger_temp': p_temp})
  };
  var response = UrlFetchApp.fetch(url, options);
  return response;
}


/**
 * Function to send API call to set heating levels on
 * different seats.
 * 
 * author: mjhwa@yahoo.com
 */
function setCarSeatHeating(vin, seat, setting) {
  var url = BASE_URL + getVehicleId(vin) + '/command/remote_seat_heater_request';
  var options = {
    "headers": {
      "authorization": "Bearer " + ACCESS_TOKEN
    },
    "method": "post",
    "contentType": "application/json",
    "payload": JSON.stringify({'heater': seat, 'level': setting})
  };
  var response = UrlFetchApp.fetch(url, options);
  return response;
}


/**
 * Function to send API call to start the vehicle HVAC.
 * 
 * author: mjhwa@yahoo.com
 */
function preconditionCarStart(vin) {
  var url = BASE_URL + getVehicleId(vin) + '/command/auto_conditioning_start';
  var options = {
    "headers": {
      "authorization": "Bearer " + ACCESS_TOKEN
    },
    "method": "post",
    'contentType': 'application/json'
  };
  var response = UrlFetchApp.fetch(url, options);
  return response;
}


/**
 * Function to send API call to stop the vehicle HVAC.
 * 
 * author: mjhwa@yahoo.com
 */
function preconditionCarStop(vin) {
  var url = BASE_URL + getVehicleId(vin) + '/command/auto_conditioning_stop';
  var options = {
    "headers": {
      "authorization": "Bearer " + ACCESS_TOKEN
    },
    "method": "post",
    'contentType': 'application/json'
  };
  var response = UrlFetchApp.fetch(url, options);
  return response;
}


/**
 * Function to send API call to get local weather data.
 * 
 * author: mjhwa@yahoo.com
 */
function getCurrentWeather(zipcode) {
  var url = 'https://api.openweathermap.org/data/2.5/weather?zip=' + zipcode + '&APPID=' + OPENWEATHERMAP_KEY + '&units=metric';
  var response = UrlFetchApp.fetch(url);
  return response;
}
