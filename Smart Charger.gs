var M3_VIN = '0123456789';  
var MX_VIN = '0123456789';  
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
function notifyIsTeslaPluggedIn() {
  try {
    // get all vehicle data to avoid repeat API calls
    var m3_data = JSON.parse(getVehicleData(M3_VIN).getContentText());
    var mx_data = JSON.parse(getVehicleData(MX_VIN).getContentText());
  
    // write data to calculate charging start times; both functions for this needs to be executed, because the calculation on the Google Sheet 
    // is dependent on values from both vehicles
    writeM3StartTimes(m3_data);
    writeMXStartTimes(mx_data);

    // get car info
    var charge_port_door_open = m3_data.response.charge_state.charge_port_door_open;
    var battery_level = m3_data.response.charge_state.battery_level;
    var battery_range = m3_data.response.charge_state.battery_range;
    
    var email_notification = Sheets.Spreadsheets.Values.get(EV_SPREADSHEET_ID, 'Smart Charger!H10').values[0];
    
    // check if email notification is set to "on" first 
    if (email_notification == 'on') {
      // send an email if the charge port door is not open, i.e. not plugged in
      if (!charge_port_door_open) {
        var message =  'Your car is not plugged in.  \n\nCurrent battery level is ' 
            message += battery_level + '%, ' 
            message += battery_range + ' estimated miles.  \n\n-Your Model 3';
        MailApp.sendEmail(email_address1, 'Please Plug In Your Model 3', message);
      } 
    }
    
    charge_port_door_open = mx_data.response.charge_state.charge_port_door_open;
    battery_level = mx_data.response.charge_state.battery_level;
    battery_range = mx_data.response.charge_state.battery_range;

    email_notification = Sheets.Spreadsheets.Values.get(EV_SPREADSHEET_ID, 'Smart Charger!H9').values[0];
    
    // check if email notification is set to "on" first 
    if (email_notification == 'on') {
      // send an email if the charge port door is not open, i.e. not plugged in
      if (!charge_port_door_open) {
        message =  'Your car is not plugged in.  \n\nCurrent battery level is ' 
        message += battery_level + '%, ' 
        message += battery_range + ' estimated miles.  \n\n-Your Model X';
        MailApp.sendEmail(email_address2, 'Please Plug In Your Model X', message, {cc: email_address1});
      }
    }
    
    // set trigger for charging 
    scheduleM3Charging(m3_data, mx_data);
    scheduleMXCharging(m3_data, mx_data);
    
    // set cabin preconditioning the next morning
    setM3Precondition(m3_data);
    setMXPrecondition(mx_data);
  } catch (e) {
    logError('notifyIsTeslaPluggedIn(): ' + e);
    wakeVehicle(M3_VIN);
    wakeVehicle(MX_VIN);
    Utilities.sleep(WAIT_TIME);
    notifyIsTeslaPluggedIn();
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
function scheduleM3Charging(m3_data, mx_data) {
  var target_soc = Number(Sheets.Spreadsheets.Values.get(EV_SPREADSHEET_ID, 'Smart Charger!B18').values[0]);
  var current_soc = Number(Sheets.Spreadsheets.Values.get(EV_SPREADSHEET_ID, 'Smart Charger!B10').values[0]);
  
  // if the target SoC is greater than the current SoC and charging state isn't Complete, create a trigger for charging
  if ((target_soc > current_soc) && (m3_data.response.charge_state.charging_state != 'Complete')) {  
    // get calculated start time depending on location of cars
    if (isVehicleAtHome(m3_data) && isVehicleAtHome(mx_data)) {
      var start_time = Sheets.Spreadsheets.Values.get(EV_SPREADSHEET_ID, 'Smart Charger!E26').values[0];
    } else if (isVehicleAtHome(m3_data) && !isVehicleAtHome(mx_data)) {
      var start_time = Sheets.Spreadsheets.Values.get(EV_SPREADSHEET_ID, 'Smart Charger!J25').values[0];
    } else {
      return;
    }
    
    // set the right date of the estimated charge time based on AM or PM
    if (start_time.toString().indexOf('AM') >= 0) {
      var tomorrow_date = new Date(Date.now() + 1000*60*60*24).toLocaleDateString();
      var estimated_charge_start_time = new Date (tomorrow_date + ' ' + start_time);
    } else {
      var estimated_charge_start_time = new Date (new Date().toLocaleDateString() + ' ' + start_time);
    }

    // if the estimated start time is after the car's onboard scheduled start time, exit
    var car_charge_schedule = new Date(tomorrow_date + ' ' + Sheets.Spreadsheets.Values.get(EV_SPREADSHEET_ID, 'Smart Charger!E27').values[0]);
    if (estimated_charge_start_time > car_charge_schedule) { return; }  
    
    // create trigger
    if (doesTriggerExist('chargeM3')) { deleteTrigger('chargeM3'); }
    ScriptApp.newTrigger('chargeM3').timeBased().at(estimated_charge_start_time).create(); 
    
    /*// send IFTTT notification
    var options = {
      'method' : 'post',
      'contentType': 'application/json',
      'payload': JSON.stringify({'value1': 'Model 3', 'value2': estimated_charge_start_time.toString()})
    };
    UrlFetchApp.fetch('https://maker.ifttt.com/trigger/set_tesla_charge_success/with/key/' + IFTTT_KEY, options);*/
    
    // send email notification
    var message = 'The Model 3 is set to charge on ' + estimated_charge_start_time.toString() + '.';
    MailApp.sendEmail(email_address1, 'Model 3 Set to Charge', message); 
    
    // create back up trigger for 15 minutes later
    if (doesTriggerExist('chargeM3Backup')) { deleteTrigger('chargeM3Backup'); }
    var estimated_backup_charge_start_time = new Date (new Date (estimated_charge_start_time).getTime() + 1000*60*15);
    ScriptApp.newTrigger('chargeM3Backup').timeBased().at(estimated_backup_charge_start_time).create();
  }
}

function scheduleMXCharging(m3_data, mx_data) {
  var target_soc = Number(Sheets.Spreadsheets.Values.get(EV_SPREADSHEET_ID, 'Smart Charger!B17').values[0]);
  var current_soc = Number(Sheets.Spreadsheets.Values.get(EV_SPREADSHEET_ID, 'Smart Charger!B9').values[0]);
  
  // if the target SoC is greater than the current SoC and charging state isn't Complete, create a trigger for charging
  if ((target_soc > current_soc) && (mx_data.response.charge_state.charging_state != 'Complete')) {  
    // get calculated start time depending on location of cars
    if (isVehicleAtHome(mx_data) && isVehicleAtHome(m3_data)) {
      var start_time = Sheets.Spreadsheets.Values.get(EV_SPREADSHEET_ID, 'Smart Charger!F26').values[0];
    } else if (isVehicleAtHome(mx_data) && !isVehicleAtHome(m3_data)) {
      var start_time = Sheets.Spreadsheets.Values.get(EV_SPREADSHEET_ID, 'Smart Charger!K26').values[0];
    } else {
      return;
    }
  
    // set the right date of the estimated charge time based on AM or PM
    if (start_time.toString().indexOf('AM') >= 0) {
      var tomorrow_date = new Date(Date.now() + 1000*60*60*24).toLocaleDateString();
      var estimated_charge_start_time = new Date (tomorrow_date + ' ' + start_time);
    } else {
      var estimated_charge_start_time = new Date (new Date().toLocaleDateString() + ' ' + start_time);
    }

    // if the estimated start time is after the car's onboard scheduled start time, exit
    var car_charge_schedule = new Date(tomorrow_date + ' ' + Sheets.Spreadsheets.Values.get(EV_SPREADSHEET_ID, 'Smart Charger!F27').values[0]);
    if (estimated_charge_start_time > car_charge_schedule) { return; }  
    
    // create trigger
    if (doesTriggerExist('chargeMX')) { deleteTrigger('chargeMX'); }
    ScriptApp.newTrigger('chargeMX').timeBased().at(estimated_charge_start_time).create(); 
    
    /*// send IFTTT notification
    var options = {
      'method' : 'post',
      'contentType': 'application/json',
      'payload': JSON.stringify({'value1': 'Model X', 'value2': estimated_charge_start_time.toString()})
    };
    UrlFetchApp.fetch('https://maker.ifttt.com/trigger/set_tesla_charge_success/with/key/' + IFTTT_KEY, options);*/
    
    // send email notification
    var message = 'The Model X is set to charge on ' + estimated_charge_start_time.toString() + '.';
    MailApp.sendEmail(email_address1, 'Model X Set to Charge', message);
    
    // create back up trigger for 15 minutes later
    if (doesTriggerExist('chargeMXBackup')) { deleteTrigger('chargeMXBackup'); }
    var estimated_backup_charge_start_time = new Date (new Date (estimated_charge_start_time).getTime() + 1000*60*15);
    ScriptApp.newTrigger('chargeMXBackup').timeBased().at(estimated_backup_charge_start_time).create();
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
function writeM3StartTimes(data) {
  var inputs = [];
  
  // write m3 range to Google Sheet
  inputs.push({
    range: 'Smart Charger!B10', 
    values: [[data.response.charge_state.battery_range]]
  });
  
  // write m3 time and date stamp to Google Sheet
  inputs.push({
    range: 'Smart Charger!D10', 
    values: [[new Date().toLocaleTimeString() + ", " + new Date().toLocaleDateString()]]
  });
  
  // write m3 scheduled charge time to Google Sheet
  inputs.push({
    range: 'Smart Charger!E28', 
    values: [[data.response.charge_state.scheduled_charging_start_time]]
  });
  
  // write m3 charge limit to Google Sheet
  inputs.push({
    range: 'Smart Charger!B16', 
    values: [[data.response.charge_state.charge_limit_soc/100]]
  });
  
  // write m3 max range
  inputs.push({
    range: 'Smart Charger!B6', 
    values: [[data.response.charge_state.battery_range/(data.response.charge_state.battery_level/100)]]
  });
  
  // batch write data to sheet
  Sheets.Spreadsheets.Values.batchUpdate({valueInputOption: 'USER_ENTERED', data: inputs}, EV_SPREADSHEET_ID);
}

function writeMXStartTimes(data) {
  var inputs = [];
  
  // write mx range to Google Sheet
  inputs.push({
    range: 'Smart Charger!B9', 
    values: [[data.response.charge_state.battery_range]]
  });
  
  // write mx time and date stamp to Google Sheet
  inputs.push({
    range: 'Smart Charger!D9', 
    values: [[new Date().toLocaleTimeString() + ", " + new Date().toLocaleDateString()]]
  });
  
  // write mx scheduled charge time to Google Sheet
  inputs.push({
    range: 'Smart Charger!F28', 
    values: [[data.response.charge_state.scheduled_charging_start_time]]
  });
  
  // write mx charge limit to Google Sheet
  inputs.push({
    range: 'Smart Charger!B15', 
    values: [[data.response.charge_state.charge_limit_soc/100]]
  });
  
  // write mx max range
  inputs.push({
    range: 'Smart Charger!B5', 
    values: [[data.response.charge_state.battery_range/(data.response.charge_state.battery_level/100)]]
  });

  // batch write data to sheet
  Sheets.Spreadsheets.Values.batchUpdate({valueInputOption: 'USER_ENTERED', data: inputs}, EV_SPREADSHEET_ID);
}

/**
 * Calculates if the distance of the car is greater than 0.25 miles away from home.  The calculation uses Haversine Formula 
 * expressed in terms of a two-argument inverse tangent function to calculate the great circle distance between two points 
 * on the Earth. This is the method recommended for calculating short distances by Bob Chamberlain (rgc@jpl.nasa.gov) 
 * of Caltech and NASA's Jet Propulsion Laboratory as described on the U.S. Census Bureau Web site.
 */
function isVehicleAtHome(data) {
  return isVehicleAtLocation(data, HOME_LAT, HOME_LNG);
}

function isVehicleAtLocation(data, lat, lng) {
  var d = getDistance(data.response.drive_state.latitude, data.response.drive_state.longitude, lat, lng);
  
  // check if the car is more than a quarter of a mile away
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

function chargeM3() {
  chargeVehicle(M3_VIN);
}

function chargeM3Backup() {
  // add check to see if car is already charging or do nothing else since sending a charge command while it's charging doesn't do anything.
  chargeVehicle(M3_VIN);
}

function chargeMX() {
  chargeVehicle(MX_VIN);
}

function chargeMXBackup() {
  // add check to see if car is already charging or do nothing else since sending a charge command while it's charging doesn't do anything.
  chargeVehicle(MX_VIN);
}

function chargeVehicle(vin) {
  try {
    var url = 'https://owner-api.teslamotors.com/api/1/vehicles/' + getVehicleId(vin) + '/command/charge_start';
    var options = {
      "headers": {
        "authorization": "Bearer " + ACCESS_TOKEN
      },
      "method": "post"
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

function wakeVehicle(vin) {
  try {
    var url = 'https://owner-api.teslamotors.com/api/1/vehicles/' + getVehicleId(vin) + '/wake_up';
    var options = {
      "headers": {
        "authorization": "Bearer " + ACCESS_TOKEN
      },
      "method": "post"
    };
    
    return UrlFetchApp.fetch(url, options);
  } catch (e) {
    logError('wakeVehicle(' + vin + '): ' + e);
    Utilities.sleep(WAIT_TIME);    
    wakeVehicle(vin)
  }
}

function getVehicleData(vin) {
  try {
    var url = 'https://owner-api.teslamotors.com/api/1/vehicles/' + getVehicleId(vin) + '/vehicle_data';
    
    var options = {
      "headers": {
        "authorization": "Bearer " + ACCESS_TOKEN
      }
    };
    var response = UrlFetchApp.fetch(url, options);
    return response;
  } catch (e) {
    logError('getVehicleData(' + vin + '): ' + e);
  }
}

function getVehicleId(vin) {
  try {
    var url = 'https://owner-api.teslamotors.com/api/1/vehicles';
    
    var options = {
      "headers": {
        "authorization": "Bearer " + ACCESS_TOKEN
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

/* This is deprecated as Tesla seems to blocking these calls from Google Apps Script.  I have a Python version of this function that works from a non-Google hosted server.
function getToken() {  // This expires periodically, I forget how long
  var email = '';  
  var password = '';  
  var passcode = '';

  try {
    // Step 1: Obtain the login page
    var code_verifier = new Array(86).join().replace(
      /(.|$)/g, 
      function() {
        return ((Math.random()*36)|0).toString(36)[Math.random()<.5?"toString":"toUpperCase"]();
      }
    );
    var code_challenge = Utilities.base64EncodeWebSafe(
      Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, code_verifier)
    );
    var url = 'https://auth.tesla.com/oauth2/v3/authorize';
        url += '?client_id=ownerapi';
        url += '&code_challenge=' + code_challenge;
        url += '&code_challenge_method=S256';
        url += '&redirect_uri=' + encodeURI('https://auth.tesla.com/void/callback');
        url += '&response_type=code';
        url += '&scope=' + encodeURI('openid email offline_access');
        url += '&state=state';
    var options = {
      'headers': {'User-Agent': 'GoogleAppsScript'},
      'method': 'get'
    };
    var response = UrlFetchApp.fetch(url, options);
    var csrf = response.getContentText().substring(
      response.getContentText().search('name="_csrf"') + 20, 
      response.getContentText().search('name="_csrf"') + 56
    );
    var phase = response.getContentText().substring(
      response.getContentText().search('name="_phase"') + 21, 
      response.getContentText().search('name="_phase"') + 33
    );
    var process = response.getContentText().substring(
      response.getContentText().search('name="_process"') + 23, 
      response.getContentText().search('name="_process"') + 24
    );
    var transaction_id = response.getContentText().substring(
      response.getContentText().search('name="transaction_id"') + 29, 
      response.getContentText().search('name="transaction_id"') + 37
    );
    var cookie = response.getAllHeaders()['Set-Cookie'];

    // Step 2: Authenticate user name and password
    var data = {
      '_csrf': csrf,
      '_phase': phase,
      '_process': process,
      'transaction_id': transaction_id,
      'cancel': '',
      'identity': email,
      'credential': password
    };
    options = {
      'headers': {'User-Agent': 'GoogleAppsScript', 'Cookie': cookie},
      'method': 'post',
      'payload': data
    };
    response = UrlFetchApp.fetch(url, options);

    // Step 3: Authenticate MFA
    url = 'https://auth.tesla.com/oauth2/v3/authorize/mfa/factors';
    url += '?transaction_id=' + transaction_id;
    options = {
      'headers': {'User-Agent': 'GoogleAppsScript', 'Cookie': cookie},
      'method': 'get'
    };
    response = UrlFetchApp.fetch(url, options);
    var factor_id = JSON.parse(response).data[0].id;
    url = 'https://auth.tesla.com/oauth2/v3/authorize/mfa/verify';
    data = {
      'factor_id': factor_id,
      'transaction_id': transaction_id,
      'passcode': passcode
    };
    options = {
      'headers': {'User-Agent': 'GoogleAppsScript', 'Cookie': cookie},
      'method': 'post',
      'contentType': 'application/json',
      'payload': JSON.stringify(data)
    };
    response = UrlFetchApp.fetch(url, options);

    // Step 4: Obtain an authorization code and exchange authorization code for bearer token
    url = 'https://auth.tesla.com/oauth2/v3/authorize';
    url += '?client_id=ownerapi';
    url += '&code_challenge=' + code_challenge;
    url += '&code_challenge_method=S256';
    url += '&redirect_uri=' + encodeURI('https://auth.tesla.com/void/callback');
    url += '&response_type=code';
    url += '&scope=' + encodeURI('openid email offline_access');
    url += '&state=state';
    data = {
      'transaction_id': transaction_id
    };
    options = {
      'headers': {'User-Agent': 'GoogleAppsScript', 'Cookie': cookie},
      'method': 'post',
      'followRedirects': false,
      'payload': data
    };
    response = UrlFetchApp.fetch(url, options);
    var code = response.getContentText().substring(
      response.getContentText().search('code') + 5, 
      response.getContentText().search('&')
    );
    url = 'https://auth.tesla.com/oauth2/v3/token';
    data = {
      'grant_type': 'authorization_code',
      'client_id': 'ownerapi',
      'code': code,
      'code_verifier': code_verifier,
      'redirect_uri': 'https://auth.tesla.com/void/callback'
    };
    options = {
      'headers': {'User-Agent': 'GoogleAppsScript', 'Cookie': cookie},
      'method': 'post',
      'contentType': 'application/json',
      'payload': JSON.stringify(data)
    };
    response = JSON.parse(UrlFetchApp.fetch(url, options));

    // Step 5: Exchange bearer token for access token
    url = 'https://owner-api.teslamotors.com/oauth/token';
    var data = {
      'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
      'client_id': '81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384',
      'client_secret': 'c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3'
    };
    var options = {
      'headers': {'authorization': 'Bearer ' + response.access_token},
      "method": "post",
      "contentType": "application/json",
      "payload": JSON.stringify(data)
    };
    response = JSON.parse(UrlFetchApp.fetch(url, options));
    Logger.log('access token: ' + response.access_token);
  } catch (e) {
    logError('getToken(): ' + e);
  }
}*/

/**
 * This checks to see if the access token expires in a week or less and will send an email reminder to get a new one.
 */
function checkTokenExpiration() {
  try {
    // get token expiration date
    var exiration_date = new Date(Sheets.Spreadsheets.Values.get(EV_SPREADSHEET_ID, 'Smart Charger!H5').values[0]);

    // get the date for the reminder (7 days prior)
    var reminder_date = new Date(exiration_date - 1000*60*60*24*7);
  //  Logger.log('reminder date: ' + reminder_date.toLocaleDateString());
  //  Logger.log('now: ' + new Date().toLocaleDateString());

    if (new Date().valueOf() >= reminder_date.valueOf()) {
      var message =  'Your Tesla Access Token is expiring on ' + exiration_date.toLocaleDateString();
          message += '.  Please generate a new token soon.';
      MailApp.sendEmail(email_address1, 'Tesla Access Token Expiring Soon', message);
    }
  } catch (e) {
    logError('checkTokenExpiration(): ' + e);
  }
}
