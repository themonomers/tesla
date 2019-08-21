var M3_VID = '0123456789';  // this is the value of the attribute “id_s”
var MX_VID = '0123456789';  // this is the value of the attribute “id_s”
var WAIT_TIME = 30000;
var R = 3958.8;  // Earth radius in miles
var HOME_LAT = 20.123456789;  // you can get this from Google Maps
var HOME_LNG = -100.12345689;  // you can get this from Google Maps
var SPREADSHEET_ID = 'abcdef0123456789';  // this can be a database
var ACCESS_TOKEN = ' abcdef0123456789';  // you get this from calling getToken() with your username and password – be careful with this!  
var IFTTT_KEY = ' abcdef0123456789';

/**
 * Checks to see if the vehicle is plugged in, inferred from the charge port door status, and sends an email to notify 
 * if it's not.
 *
 * Also sets trigger to manually start charging at the calculated date and time. Skips if it's not within 0.25 miles from home.
 */
function notifyIsM3PluggedIn() {
  try {
    // write data to calculate charging start time if it's been more than an hour since the last update
    var update_period = new Date(new Date(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Charger!D10').values[0]).getTime() + 1000*60*60*1);
    if (new Date() > update_period) {
      writeStartTimes();
    }
    
    // get car info
    var data = JSON.parse(getVehicleChargeState(M3_VID).getContentText());
    var charge_port_door_open = data.response.charge_port_door_open;
    var battery_level = data.response.battery_level;
    var battery_range = data.response.battery_range;
    
    // send an email if the charge port door is not open, i.e. not plugged in
    if (!charge_port_door_open) {
      var message = 'Your car is not plugged in.  \n\nCurrent battery level is ' + battery_level + '%, ' + battery_range + ' estimated miles.  \n\n-Your Model 3';
      MailApp.sendEmail('email@email.com', 'Please Plug In Your Model 3', message);
    } 
    
    // set trigger for charging if the car is home and charging state isn't Complete
    if (isM3Home() && (data.response.charging_state != 'Complete')) {
      scheduleM3Charging();
    }
  } catch (e) {
    logError(e);

    wakeVehicle(M3_VID);
    Utilities.sleep(WAIT_TIME);
    notifyIsM3PluggedIn();
  }
}

function notifyIsMXPluggedIn() {
  try {
    // write data to calculate charging start time if it's been more than an hour since the last update
    var update_period = new Date(new Date(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Charger!D9').values[0]).getTime() + 1000*60*60*1);
    if (new Date() > update_period) {
      writeStartTimes();
    }
    
    // get car info
    var data = JSON.parse(getVehicleChargeState(MX_VID).getContentText());
    var charge_port_door_open = data.response.charge_port_door_open;
    var battery_level = data.response.battery_level;
    var battery_range = data.response.battery_range;
    
    // send an email if the charge port door is not open, i.e. not plugged in
    if (!charge_port_door_open) {
      var message = 'Your car is not plugged in.  \n\nCurrent battery level is ' + battery_level + '%, ' + battery_range + ' estimated miles.  \n\n-Your Model X';
      MailApp.sendEmail('email@email.com', 'Please Plug In Your Model X', message, {cc: 'email@email.com'});
    }
    
    // set trigger for charging if the car is home and charging state isn't Complete
    if (isMXHome() && (data.response.charging_state != 'Complete')) {
      scheduleMXCharging();
    }
  } catch (e) {
    logError(e);

    wakeVehicle(MX_VID);
    Utilities.sleep(WAIT_TIME);
    notifyIsMXPluggedIn();
  }
}

/**
 * Called by a trigger to read vehicle range and estimated charge start time from a Google Sheet, then create a trigger 
 * to execute at a specific date and time.  The trigger will call a function to wake up the vehicle and send a command 
 * to start charging. 
 *
 * Since there's isn't an API yet to set the vehicle's scheduled charge time, this workaround is to set the time as 
 * "late" (5a) as possible in the vehicle console, then have this function set up a trigger to manually start charging 
 * the car at the optimal time.
 * 
 * When an API is available to set scheduled charge times, this function won't need to be run on
 * a trigger and can be set in the car.
 */
function scheduleM3Charging() {
  var target_soc = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Charger!B18').values[0]);
  var current_soc = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Charger!B10').values[0]);
  
  // if the target SoC is greater than the current SoC, create a trigger for charging
  if (target_soc > current_soc) {  
    // get calculated start time
    var start_time = Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Charger!E26').values[0];

    // set the right date of the estimated charge time based on AM or PM
    if (start_time.toString().indexOf('AM') >= 0) {
      var tomorrowDate = new Date(Date.now() + 1000*60*60*24).toLocaleDateString();
      var estimatedChargeStartTime = new Date (tomorrowDate + ' ' + start_time + ' -0700');
    } else {
      var estimatedChargeStartTime = new Date (new Date().toLocaleDateString() + ' ' + start_time + ' -0700');
    }
    
    // create trigger
    ScriptApp.newTrigger('chargeM3').timeBased().at(estimatedChargeStartTime).create();
    
    // create back up trigger for 15 minutes later
    var estimatedBackupChargeStartTime = new Date (new Date (estimatedChargeStartTime).getTime() + 1000*60*15);
    ScriptApp.newTrigger('chargeM3Backup').timeBased().at(estimatedBackupChargeStartTime).create();
    
    // send IFTTT notification
    var options = {
      'method' : 'post',
      'contentType': 'application/json',
      'payload': JSON.stringify({'value1': 'Model 3', 'value2': estimatedChargeStartTime.toString()})
    };
    UrlFetchApp.fetch('https://maker.ifttt.com/trigger/set_tesla_charge_success/with/key/' + IFTTT_KEY, options);
  }
}

function scheduleMXCharging() {
  var target_soc = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Charger!B17').values[0]);
  var current_soc = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Charger!B9').values[0]);
  
  // if the target SoC is greater than the current SoC, create a trigger for charging
  if (target_soc > current_soc) {  
    // get calculated start time
    var start_time = Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Charger!F26').values[0];
  
    // set the right date of the estimated charge time based on AM or PM
    if (start_time.toString().indexOf('AM') >= 0) {
      var tomorrowDate = new Date(Date.now() + 1000*60*60*24).toLocaleDateString();
      var estimatedChargeStartTime = new Date (tomorrowDate + ' ' + start_time + ' -0700');
    } else {
      var estimatedChargeStartTime = new Date (new Date().toLocaleDateString() + ' ' + start_time + ' -0700');
    }
    
    // create trigger
    ScriptApp.newTrigger('chargeMX').timeBased().at(estimatedChargeStartTime).create();
    
    // create back up trigger for 15 minutes later
    var estimatedBackupChargeStartTime = new Date (new Date (estimatedChargeStartTime).getTime() + 1000*60*15);
    ScriptApp.newTrigger('chargeMXBackup').timeBased().at(estimatedBackupChargeStartTime).create();
    
    // send IFTTT notification
    var options = {
      'method' : 'post',
      'contentType': 'application/json',
      'payload': JSON.stringify({'value1': 'Model X', 'value2': estimatedChargeStartTime.toString()})
    };
    UrlFetchApp.fetch('https://maker.ifttt.com/trigger/set_tesla_charge_success/with/key/' + IFTTT_KEY, options);
  }
}

/**
 * Writes to a Google Sheet that calculates optimum charging start times for 2 vehicles to reach the target SoC by 6:00AM 
 * (1 hour buffer until 7:00AM).
 *
 * This needs to be executed in one function, serially, because the calculation on the Google Sheet is dependent on values 
 * from both vehicles.  If these are called separately, they will complete asynchronously which may give inaccurate start 
 * times.
 */
function writeStartTimes() {
  var inputs = [];
  
  try {
    // get vehicle charge data
    var data = JSON.parse(getVehicleChargeState(M3_VID).getContentText());
    
    // write m3 range to Google Sheet
    inputs.push({range: 'Smart Charger!B10', values: [[data.response.battery_range]]});
    
    // write m3 time and date stamp to Google Sheet
    inputs.push({range: 'Smart Charger!D10', values: [[new Date().toLocaleTimeString() + ", " + new Date().toLocaleDateString()]]});
    
    // write m3 scheduled charge time to Google Sheet
    inputs.push({range: 'Smart Charger!E28', values: [[data.response.scheduled_charging_start_time]]});
    
    // write m3 charge limit to Google Sheet
    inputs.push({range: 'Smart Charger!B16', values: [[data.response.charge_limit_soc/100]]});
    
    // write m3 max range
    inputs.push({range: 'Smart Charger!B6', values: [[data.response.battery_range/(data.response.battery_level/100)]]});
    
    // write this into telemetry sheet to track battery degradation, since we already got this data
    var open_row = findOpenRow(SPREADSHEET_ID, 'Telemetry','A:A');
    inputs.push({range: 'Telemetry!M' + (open_row - 1), values: [[data.response.battery_range/(data.response.battery_level/100)]]});
      
    // copy degradation formula down
    SpreadsheetApp.openById(SPREADSHEET_ID).getRange('Telemetry!N3').copyTo(SpreadsheetApp.openById(SPREADSHEET_ID).getRange('Telemetry!N' + (open_row - 1)));
  } catch (e) {
    logError(e);
    
    wakeVehicle(M3_VID);
    Utilities.sleep(WAIT_TIME);
    writeStartTimes();
  }
    
  try {    
    // get vehicle charge data
    data = JSON.parse(getVehicleChargeState(MX_VID).getContentText());
    
    // write mx range to Google Sheet
    inputs.push({range: 'Smart Charger!B9', values: [[data.response.battery_range]]});
    
    // write mx time and date stamp to Google Sheet
    inputs.push({range: 'Smart Charger!D9', values: [[new Date().toLocaleTimeString() + ", " + new Date().toLocaleDateString()]]});
    
    // write mx scheduled charge time to Google Sheet
    inputs.push({range: 'Smart Charger!F28', values: [[data.response.scheduled_charging_start_time]]});
    
    // write mx charge limit to Google Sheet
    inputs.push({range: 'Smart Charger!B15', values: [[data.response.charge_limit_soc/100]]});
    
    // write mx max range
    inputs.push({range: 'Smart Charger!B5', values: [[data.response.battery_range/(data.response.battery_level/100)]]});
    
    // write this into telemetry sheet to track battery degradation, since we already got this data
    open_row = findOpenRow(SPREADSHEET_ID, 'Telemetry','Q:Q');
    inputs.push({range: 'Telemetry!AC' + (open_row - 1), values: [[data.response.battery_range/(data.response.battery_level/100)]]});
      
    // copy degradation formula down
    SpreadsheetApp.openById(SPREADSHEET_ID).getRange('Telemetry!AD3').copyTo(SpreadsheetApp.openById(SPREADSHEET_ID).getRange('Telemetry!AD' + (open_row - 1)));
  } catch (e) {
    logError(e);
    
    wakeVehicle(MX_VID);
    Utilities.sleep(WAIT_TIME);
    writeStartTimes();
  }

  // batch write data to sheet
  Sheets.Spreadsheets.Values.batchUpdate({valueInputOption: 'USER_ENTERED', data: inputs}, SPREADSHEET_ID);
}

/**
 * Calculates if the distance of the car is greater than 0.25 miles away from home.  The calculation uses Haversine Formula 
 * expressed in terms of a two-argument inverse tangent function to calculate the great circle distance between two points 
 * on the Earth. This is the method recommended for calculating short distances by Bob Chamberlain (rgc@jpl.nasa.gov) 
 * of Caltech and NASA's Jet Propulsion Laboratory as described on the U.S. Census Bureau Web site.
 */
function isM3Home() { 
  var data = JSON.parse(getVehicleDriveState(M3_VID).getContentText());
  //    var timestamp = data.response.gps_as_of;
  var d = getDistanceFromHome(data.response.latitude, data.response.longitude);
  
  // check if the car is more than a quarter of a mile away from home
  if (d < 0.25) {
    return true;
  } else {
    return false;
  }
}

function isMXHome() { 
  var data = JSON.parse(getVehicleDriveState(MX_VID).getContentText());
  
  var d = getDistanceFromHome(data.response.latitude, data.response.longitude);
  
  // check if the car is more than a quarter of a mile away from home
  if (d < 0.25) {
    return true;
  } else {
    return false;
  }
}

function chargeM3() {
  try {
    chargeVehicle(M3_VID);
  } catch (e) {
    logError(e);
    
    wakeVehicle(M3_VID)
    Utilities.sleep(WAIT_TIME);
    chargeM3();
  }
}

function chargeM3Backup() {
  try {
    // add check to see if car is already charging or do nothing else since sending a charge command while it's charging doesn't do anything.
    chargeVehicle(M3_VID);
  } catch (e) {
    logError(e);
    
    wakeVehicle(M3_VID)
    Utilities.sleep(WAIT_TIME);
    chargeM3();
  }
}

function chargeMX() {
  try {
    chargeVehicle(MX_VID);
  } catch (e) {
    logError(e);
    
    wakeVehicle(MX_VID)
    Utilities.sleep(WAIT_TIME);
    chargeMX();
  }
}

function chargeMXBackup() {
  try {
    // add check to see if car is already charging or do nothing else since sending a charge command while it's charging doesn't do anything.
    chargeVehicle(MX_VID);
  } catch (e) {
    logError(e);
    
    wakeVehicle(MX_VID)
    Utilities.sleep(WAIT_TIME);
    chargeMX();
  }
}

function getDistanceFromHome(car_lat, car_lng) {
  var diff_lat = toRad(car_lat - HOME_LAT);
  var diff_lng = toRad(car_lng - HOME_LNG);  
  
  var a = (Math.sin(diff_lat/2) * Math.sin(diff_lat/2)) + Math.cos(HOME_LAT) * Math.cos(car_lat) * (Math.sin(diff_lng/2) * Math.sin(diff_lng/2));
  var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  var d = R * c;
  
  return d;
}

function toRad(x) {
  return x * Math.PI / 180;
}

function getVehicleDriveState(vid) {
  var url = 'https://owner-api.teslamotors.com/api/1/vehicles/' + vid + '/data_request/drive_state';
  
  var options = {
    "headers": {
      "authorization": "Bearer " + ACCESS_TOKEN
    }
  };
  
  return UrlFetchApp.fetch(url, options);
}

function getVehicleChargeState(vid) {
  var url = 'https://owner-api.teslamotors.com/api/1/vehicles/' + vid + '/data_request/charge_state';
  
  var options = {
    "headers": {
      "authorization": "Bearer " + ACCESS_TOKEN
    }
  };

  return UrlFetchApp.fetch(url, options);
}

function chargeVehicle(vid) {
  var url = 'https://owner-api.teslamotors.com/api/1/vehicles/' + vid + '/command/charge_start';
  var options = {
    "headers": {
      "authorization": "Bearer " + ACCESS_TOKEN
    },
    "method": "post"
  };
  
  return UrlFetchApp.fetch(url, options);
}

function wakeVehicle(vid) {
  try {
    var url = 'https://owner-api.teslamotors.com/api/1/vehicles/' + vid + '/wake_up';
    var options = {
      "headers": {
        "authorization": "Bearer " + ACCESS_TOKEN
      },
      "method": "post"
    };
    
    return UrlFetchApp.fetch(url, options);
  } catch (e) {
    logError(e);

    Utilities.sleep(WAIT_TIME);    
    wakeVehicle(vid)
  }
}

function getVehicles() {
  var url = 'https://owner-api.teslamotors.com/api/1/vehicles';
  
  var options = {
    "headers": {
      "authorization": "Bearer " + ACCESS_TOKEN
    }
  };

  return UrlFetchApp.fetch(url, options);
}

function getToken() {  // This expires periodically, I forget how long
  var email = '';  // I suggest not storing this here, at least not until 2FA
  var password = '';  // I suggest not storing this here, at least not until 2FA
  var url = 'https://owner-api.teslamotors.com/oauth/token?grant_type=password';

  var data = {
    "client_id": "81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384",
    "client_secret": "c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3",
    "email": email,
    "password": password
  };  // not sure how often client_id and client_secret changes, if at all
  
  var options = {
    "method": "post",
    "contentType": "application/json",
    "payload": JSON.stringify(data),
    muteHttpExceptions: true
  };
  
  return UrlFetchApp.fetch(url, options);
}
