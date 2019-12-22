var OPENWEATHERMAP_KEY = 'abcdef0123456789';

/**
 * Runs every night to see if it should create a trigger for the following morning, currently just based on if the car is at home.
 *
 */
function setPrecondition() {
  var tomorrowDate = new Date(Date.now() + 1000*60*60*24).toLocaleDateString();

  try {
    // check if the car is with 0.25 miles of home
    if (isM3Home()) {
      // get start and stop time preferences
      var start_time = Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!B20').values[0];
      var stop_time = Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!B21').values[0];
      
      // specific date/time to create a trigger for tomorrow morning at the preferred start time and stop time
      var estimatedChargeStartTime = new Date (tomorrowDate + ' ' + start_time);
      var estimatedChargeStopTime = new Date (tomorrowDate + ' ' + stop_time);
      
      // create triggers
      if (!doesTriggerExist('preconditionM3Start')) { ScriptApp.newTrigger('preconditionM3Start').timeBased().at(estimatedChargeStartTime).create(); }
      if (!doesTriggerExist('preconditionM3Stop')) { ScriptApp.newTrigger('preconditionM3Stop').timeBased().at(estimatedChargeStopTime).create(); }
    }
  } catch (e) {
    logError(e);

    wakeVehicle(M3_VIN);
    Utilities.sleep(WAIT_TIME);
    setPrecondition();
  }

  try {
    // check if the car is with 0.25 miles of home
    if (isMXHome()) {        
      // get start and stop time preferences
      var start_time = Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!I20').values[0];
      var stop_time = Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!I21').values[0];
      
      // specific date/time to create a trigger for tomorrow morning at the preferred start time and stop time
      var estimatedChargeStartTime = new Date (tomorrowDate + ' ' + start_time);
      var estimatedChargeStopTime = new Date (tomorrowDate + ' ' + stop_time);
      
      // create triggers
      if (!doesTriggerExist('preconditionMXStart')) { ScriptApp.newTrigger('preconditionMXStart').timeBased().at(estimatedChargeStartTime).create(); }
      if (!doesTriggerExist('preconditionMXStop')) { ScriptApp.newTrigger('preconditionMXStop').timeBased().at(estimatedChargeStopTime).create(); }
    }
  } catch (e) {
    logError(e);

    wakeVehicle(MX_VIN);
    Utilities.sleep(WAIT_TIME);
    setPrecondition();
  }
}

/**
 * Checks a Google Sheet for heating and cooling preferences and sends a command to precondition the car.  Includes seat heating preferences.
 * Originally this just used the inside car temp but to also account for the outside temperature, it might be more comfortable for the occupants 
 * to look at the average of the two to determine when to pre-heat/cool.
 *
 * Trying to use a weather API instead of the inside or outside temp data from the cars.  The temp data from the cars don't seem to be accurate enough 
 * and not representative of passenger comfort of when to pre-heat/cool.
 *
 */
function preconditionM3Start() {
  try {
    if (!isM3Home()) { return; } // no need to execute if unsure where the car is or if it's in motion
    
    // get local weather
    var data = JSON.parse(getWeather('12345').getContentText());
    
    // get data
    var cold_temp_threshold = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!B22').values[0]);
    var hot_temp_threshold = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!B23').values[0]);
//    var data = JSON.parse(getVehicleClimateState(M3_VIN).getContentText()); 
    
    // get today's day of week to compare against Google Sheet temp preferences for that day
    var day_of_week = new Date().getDay();
    var d_temp;
    var p_temp;
    var seats = [];

    // compare temp readings and threshold to determine heating or cooling temps to use
    if (data.main.temp < cold_temp_threshold) {
      // get pre-heat preferences
      if (day_of_week == 0) {  // Sunday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!B9').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!C9').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!D9').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!E9').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!F9').values[0]));
        seats.push(-1); // skip index 3 as it's not assigned in the API
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!G9').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!H9').values[0]));
      } else if (day_of_week == 1) {  // Monday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!B3').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!C3').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!D3').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!E3').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!F3').values[0]));
        seats.push(-1); // skip index 3 as it's not assigned in the API
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!G3').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!H3').values[0]));
      } else if (day_of_week == 2) {  // Tuesday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!B4').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!C4').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!D4').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!E4').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!F4').values[0]));
        seats.push(-1); // skip index 3 as it's not assigned in the API
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!G4').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!H4').values[0]));
      } else if (day_of_week == 3) {  // Wednesday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!B5').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!C5').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!D5').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!E5').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!F5').values[0]));
        seats.push(-1); // skip index 3 as it's not assigned in the API
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!G5').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!H5').values[0]));
      } else if (day_of_week == 4) {  // Thursday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!B6').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!C6').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!D6').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!E6').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!F6').values[0]));
        seats.push(-1); // skip index 3 as it's not assigned in the API
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!G6').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!H6').values[0]));
      } else if (day_of_week == 5) {  // Friday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!B7').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!C7').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!D7').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!E7').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!F7').values[0]));
        seats.push(-1); // skip index 3 as it's not assigned in the API
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!G7').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!H7').values[0]));
      } else if (day_of_week == 6) {  // Saturday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!B8').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!C8').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!D8').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!E8').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!F8').values[0]));
        seats.push(-1); // skip index 3 as it's not assigned in the API
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!G8').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!H8').values[0]));
      } else {
        return;
      }
    } else if (data.main.temp > hot_temp_threshold) {
      // get pre-cool preferences
      if (day_of_week == 0) {  // Sunday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!B18').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!C18').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!D18').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!E18').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!F18').values[0]));
        seats.push(-1); // skip index 3 as it's not assigned in the API
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!G18').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!H18').values[0]));
      } else if (day_of_week == 1) {  // Monday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!B12').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!C12').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!D12').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!E12').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!F12').values[0]));
        seats.push(-1); // skip index 3 as it's not assigned in the API
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!G12').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!H12').values[0]));
      } else if (day_of_week == 2) {  // Tuesday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!B13').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!C13').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!D13').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!E13').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!F13').values[0]));
        seats.push(-1); // skip index 3 as it's not assigned in the API
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!G13').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!H13').values[0]));
      } else if (day_of_week == 3) {  // Wednesday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!B14').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!C14').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!D14').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!E14').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!F14').values[0]));
        seats.push(-1); // skip index 3 as it's not assigned in the API
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!G14').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!H14').values[0]));
      } else if (day_of_week == 4) {  // Thursday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!B15').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!C15').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!D15').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!E15').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!F15').values[0]));
        seats.push(-1); // skip index 3 as it's not assigned in the API
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!G15').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!H15').values[0]));
      } else if (day_of_week == 5) {  // Friday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!B16').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!C16').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!D16').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!E16').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!F16').values[0]));
        seats.push(-1); // skip index 3 as it's not assigned in the API
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!G16').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!H16').values[0]));
      } else if (day_of_week == 6) {  // Saturday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!B17').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!C17').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!D17').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!E17').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!F17').values[0]));
        seats.push(-1); // skip index 3 as it's not assigned in the API
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!G17').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!H17').values[0]));
      } else {
        return;
      }
    } else {
      return; // outside temp is within cold and hot thresholds so no preconditioning required; inside and outside car temp readings seem to be inaccurate until the HVAC runs
    }
  
    // set driver and passenger temps
    setCarTemp(M3_VIN, d_temp, p_temp);
    
    // send command to start auto conditioning
    preconditionCarStart(M3_VIN);  
      
    // set seat heater settings
    for (var i = 0; i < seats.length; i++) {
      if (i == 3) { i++; } // skip index 3 as it's not assigned in the API
      setCarSeatHeating(M3_VIN, i, seats[i]);
    }
  } catch (e) {
    logError(e);

    wakeVehicle(M3_VIN);
    Utilities.sleep(WAIT_TIME);
    preconditionM3Start();
  }
}

function preconditionMXStart() {
  try {
    if (!isMXHome()) { return; }  // no need to execute if unsure where the car is or if it's in motion
    
    // get local weather
    var data = JSON.parse(getWeather('12345').getContentText());
    
    // get data
    var cold_temp_threshold = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!I22').values[0]);
    var hot_temp_threshold = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!I23').values[0]);
//    var data = JSON.parse(getVehicleClimateState(MX_VIN).getContentText()); 
    
    // get today's day of week to compare against Google Sheet temp preferences for that day
    var day_of_week = new Date().getDay();
    var d_temp;
    var p_temp;
    var seats = [];

    // compare temp readings and threshold to determine heating or cooling temps to use
    if (data.main.temp < cold_temp_threshold) {
      // get pre-heat preferences
      if (day_of_week == 0) {  // Sunday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!I9').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!J9').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!K9').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!L9').values[0]));
      } else if (day_of_week == 1) {  // Monday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!I3').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!J3').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!K3').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!L3').values[0]));
      } else if (day_of_week == 2) {  // Tuesday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!I4').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!J4').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!K4').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!L4').values[0]));
      } else if (day_of_week == 3) {  // Wednesday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!I5').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!J5').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!K5').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!L5').values[0]));
      } else if (day_of_week == 4) {  // Thursday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!I6').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!J6').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!K6').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!L6').values[0]));
      } else if (day_of_week == 5) {  // Friday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!I7').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!J7').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!K7').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!L7').values[0]));
      } else if (day_of_week == 6) {  // Saturday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!I8').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!J8').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!K8').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!L8').values[0]));
      } else {
        return;
      }
    } else if (data.main.temp > hot_temp_threshold) {
      // get pre-cool preferences
      if (day_of_week == 0) {  // Sunday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!I18').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!J18').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!K18').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!L18').values[0]));
      } else if (day_of_week == 1) {  // Monday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!I12').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!J12').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!K12').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!L12').values[0]));
      } else if (day_of_week == 2) {  // Tuesday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!I13').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!J13').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!K13').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!L13').values[0]));
      } else if (day_of_week == 3) {  // Wednesday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!I14').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!J14').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!K14').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!L14').values[0]));
      } else if (day_of_week == 4) {  // Thursday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!I15').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!J15').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!K15').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!L15').values[0]));
      } else if (day_of_week == 5) {  // Friday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!I16').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!J16').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!K16').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!L16').values[0]));
      } else if (day_of_week == 6) {  // Saturday
        d_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!I17').values[0]);
        p_temp = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!J17').values[0]);
        
        if (isNaN(d_temp) || isNaN(p_temp)) { return; }
        
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!K17').values[0]));
        seats.push(Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Climate!L17').values[0]));
      } else {
        return;
      }
    } else {
      return; // outside temp is within cold and hot thresholds so no preconditioning required; inside and outside car temp readings seem to be inaccurate until the HVAC runs
    }
  
    // set driver and passenger temps
    setCarTemp(MX_VIN, d_temp, p_temp);
   
    // send command to start auto conditioning
    preconditionCarStart(MX_VIN);  
      
    // set seat heater settings
    for (var i = 0; i < seats.length; i++) {
      setCarSeatHeating(MX_VIN, i, seats[i]);
    }
  } catch (e) {
    logError(e);

    wakeVehicle(MX_VIN);
    Utilities.sleep(WAIT_TIME);
    preconditionMXStart();
  }
}

function preconditionM3Stop() {
  try {
    if (!isM3Home()) { return; } // no need to execute if unsure where the car is or if it's in motion
    preconditionCarStop(M3_VIN);
  } catch (e) {
    logError(e);

    wakeVehicle(M3_VIN);
    Utilities.sleep(WAIT_TIME);
    preconditionM3Stop();
  }
}

function preconditionMXStop() {
  try {
    if (!isMXHome()) { return; } // no need to execute if unsure where the car is or if it's in motion
    preconditionCarStop(MX_VIN);
  } catch (e) {
    logError(e);

    wakeVehicle(MX_VIN);
    Utilities.sleep(WAIT_TIME);
    preconditionMXStop();
  }
}

function setCarTemp(vin, d_temp, p_temp) {
  var url = 'https://owner-api.teslamotors.com/api/1/vehicles/' + getVehicleId(vin) + '/command/set_temps';
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

function setCarSeatHeating(vin, seat, setting) {
  var url = 'https://owner-api.teslamotors.com/api/1/vehicles/' + getVehicleId(vin) + '/command/remote_seat_heater_request';
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

function preconditionCarStart(vin) {
  var url = 'https://owner-api.teslamotors.com/api/1/vehicles/' + getVehicleId(vin) + '/command/auto_conditioning_start';
  var options = {
    "headers": {
      "authorization": "Bearer " + ACCESS_TOKEN
    },
    "method": "post"
  };
  var response = UrlFetchApp.fetch(url, options);
  return response;
}

function preconditionCarStop(vin) {
  var url = 'https://owner-api.teslamotors.com/api/1/vehicles/' + getVehicleId(vin) + '/command/auto_conditioning_stop';
  var options = {
    "headers": {
      "authorization": "Bearer " + ACCESS_TOKEN
    },
    "method": "post"
  };
  var response = UrlFetchApp.fetch(url, options);
  return response;
}

function getWeather(zipcode) {
  var url = 'https://api.openweathermap.org/data/2.5/weather?zip=' + zipcode + '&APPID=' + OPENWEATHERMAP_KEY + '&units=metric';
  var response = UrlFetchApp.fetch(url);
  return response;
}
