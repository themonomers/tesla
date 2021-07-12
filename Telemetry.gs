/**
 * Contains functions to read/write the vehicle's data, e.g. mileage, efficiency, etc. into a Google Sheet for tracking, 
 * analysis, and graphs.
 */
function writeM3Telemetry() { 
  try {
    // get rollup of vehicle data
    var data = JSON.parse(getVehicleData(M3_VIN).getContentText());  
    
    var inputs = [];
    // write odometer value
    var open_row = findOpenRow(EV_SPREADSHEET_ID, 'Telemetry','A:A');
    inputs.push({range: 'Telemetry!A' + open_row, values: [[data.response.vehicle_state.odometer]]});
   
    // write date stamp
    inputs.push({range: 'Telemetry!B' + open_row, values: [[new Date().toLocaleDateString()]]});

    // copy mileage formulas down
    SpreadsheetApp.openById(EV_SPREADSHEET_ID).getRange('Telemetry!C3:G3').copyTo(SpreadsheetApp.openById(EV_SPREADSHEET_ID).getRange('Telemetry!C' + (open_row - 1) + ':G' + (open_row - 1)));
    
    // write max battery capacity
    inputs.push({
      range: 'Telemetry!M' + (open_row - 1), 
      values: [[data.response.charge_state.battery_range/(data.response.charge_state.battery_level/100)]]
    });
    
    // copy down battery degradation % formula
    SpreadsheetApp.openById(EV_SPREADSHEET_ID).getRange('Telemetry!N3').copyTo(SpreadsheetApp.openById(EV_SPREADSHEET_ID).getRange('Telemetry!N' + (open_row - 1)));    

    // write target SoC %
    inputs.push({range: 'Telemetry!O' + (open_row), values: [[data.response.charge_state.charge_limit_soc/100]]});
    
    // write data for efficiency calculation
    var starting_range = data.response.charge_state.battery_range/(data.response.charge_state.battery_level/100) * data.response.charge_state.charge_limit_soc/100;
    var eod_range = data.response.charge_state.battery_range;
    
    // if the starting range is less than eod range or the car is not plugged in or charging state is complete, the starting range is equal to the 
    // eod range because it won't charge
    if (
      (starting_range < eod_range) || 
      (data.response.charge_state.charge_port_door_open == false) || 
      (data.response.charge_state.charging_state == 'Complete')
    ) {
      starting_range = eod_range;
    }
    
    // write the starting_range for the next day   
    inputs.push({range: 'Telemetry!H' + open_row, values: [[starting_range]]});
    inputs.push({range: 'Telemetry!I' + (open_row - 1), values: [[eod_range]]});
 
    // copy efficiency formulas down
    SpreadsheetApp.openById(EV_SPREADSHEET_ID).getRange('Telemetry!J3:L3').copyTo(SpreadsheetApp.openById(EV_SPREADSHEET_ID).getRange('Telemetry!J' + (open_row - 1) + ':L' + (open_row - 1)));
    
    // write temperature data into telemetry sheet
    var inside_temp = data.response.climate_state.inside_temp * 9/5 + 32;  // convert to Fahrenheit
    var outside_temp = data.response.climate_state.outside_temp * 9/5 + 32;

    inputs.push({range: 'Telemetry!P' + (open_row - 1), values: [[inside_temp]]});
    inputs.push({range: 'Telemetry!Q' + (open_row - 1), values: [[outside_temp]]});

    // batch write data to sheet
    Sheets.Spreadsheets.Values.batchUpdate({valueInputOption: 'USER_ENTERED', data: inputs}, EV_SPREADSHEET_ID);
    
    /*// send IFTTT notification
    UrlFetchApp.fetch('https://maker.ifttt.com/trigger/write_tesla_telemetry_success/with/key/' + IFTTT_KEY + '?value1=Model 3', {});*/
    // send email notification
    var timezone = Session.getScriptTimeZone();
    var time = Utilities.formatDate(new Date(), timezone, "MMMM dd, yyyy h:mm:ss a");
    var message = 'Model 3 telemetry successfully logged on ' + time + '.';
    MailApp.sendEmail(email_address1, 'Model 3 Telemetry Logged', message);
  } catch (e) {
    logError('writeM3Telemetry(): ' + e);
    wakeVehicle(M3_VIN);
    Utilities.sleep(WAIT_TIME);
    writeM3Telemetry();
  }
}

function writeMXTelemetry() { 
  try {
    // get rollup of vehicle data
    var data = JSON.parse(getVehicleData(MX_VIN).getContentText());  
    
    var inputs = [];
    // write odometer value
    var open_row = findOpenRow(EV_SPREADSHEET_ID, 'Telemetry','R:R');
    inputs.push({range: 'Telemetry!R' + open_row, values: [[data.response.vehicle_state.odometer]]});
    
    // write date stamp
    inputs.push({range: 'Telemetry!S' + open_row, values: [[new Date().toLocaleDateString()]]});
    
    // copy mileage formulas down
    SpreadsheetApp.openById(EV_SPREADSHEET_ID).getRange('Telemetry!T3:X3').copyTo(SpreadsheetApp.openById(EV_SPREADSHEET_ID).getRange('Telemetry!T' + (open_row - 1) + ':X' + (open_row - 1)));
    
    // write max battery capacity
    inputs.push({
      range: 'Telemetry!AD' + (open_row - 1), 
      values: [[data.response.charge_state.battery_range/(data.response.charge_state.battery_level/100)]]
    });

    // copy down battery degradation % formula
    SpreadsheetApp.openById(EV_SPREADSHEET_ID).getRange('Telemetry!AE3').copyTo(SpreadsheetApp.openById(EV_SPREADSHEET_ID).getRange('Telemetry!AE' + (open_row - 1)));    

    // write target SoC %
    inputs.push({range: 'Telemetry!AF' + (open_row), values: [[data.response.charge_state.charge_limit_soc/100]]});

    // write data for efficiency calculation
    var starting_range = data.response.charge_state.battery_range/(data.response.charge_state.battery_level/100) * data.response.charge_state.charge_limit_soc/100;
    var eod_range = data.response.charge_state.battery_range;
    
    // if the starting range is less than eod range or the car is not plugged in or charging state is complete, the starting range is equal to the 
    // eod range because it won't charge
    if (
      (starting_range < eod_range) || 
      (data.response.charge_state.charge_port_door_open == false) || 
      (data.response.charge_state.charging_state == 'Complete')
    ) {
      starting_range = eod_range;
    }

    // write the starting_range for the next day
    inputs.push({range: 'Telemetry!Y' + open_row, values: [[starting_range]]});
    inputs.push({range: 'Telemetry!Z' + (open_row - 1), values: [[eod_range]]});
  
    // copy efficiency formulas down
    SpreadsheetApp.openById(EV_SPREADSHEET_ID).getRange('Telemetry!AA3:AC3').copyTo(SpreadsheetApp.openById(EV_SPREADSHEET_ID).getRange('Telemetry!AA' + (open_row - 1) + ':AC' + (open_row - 1)));

    // write temperature data into telemetry sheet
    var inside_temp = data.response.climate_state.inside_temp * 9/5 + 32;  // convert to Fahrenheit
    var outside_temp = data.response.climate_state.outside_temp * 9/5 + 32;

    inputs.push({range: 'Telemetry!AG' + (open_row - 1), values: [[inside_temp]]});
    inputs.push({range: 'Telemetry!AH' + (open_row - 1), values: [[outside_temp]]});
    
    // batch write data to sheet
    Sheets.Spreadsheets.Values.batchUpdate({valueInputOption: 'USER_ENTERED', data: inputs}, EV_SPREADSHEET_ID);
    
    /*// send IFTTT notification
    UrlFetchApp.fetch('https://maker.ifttt.com/trigger/write_tesla_telemetry_success/with/key/' + IFTTT_KEY + '?value1=Model X', {});*/
    // send email notification
    var timezone = Session.getScriptTimeZone();
    var time = Utilities.formatDate(new Date(), timezone, "MMMM dd, yyyy h:mm:ss a");
    var message = 'Model X telemetry successfully logged on ' + time + '.';
    MailApp.sendEmail(email_address1, 'Model X Telemetry Logged', message);
  } catch (e) {
    logError('writeMXTelemetry(): ' + e);
    wakeVehicle(MX_VIN);
    Utilities.sleep(WAIT_TIME);
    writeMXTelemetry();
  }
}

/**
 * Looks for the next empty cell in a Google Sheet row to avoid overwriting data when reading/writing values.
 */
function findOpenRow(sheetId, sheetName, range) {
  var values = Sheets.Spreadsheets.Values.get(sheetId, sheetName + '!' + range).values;
  if (!values) {
    return 1;
  }
  return values.length + 1;
}

/**
 * Looks to see if a trigger exists.
 */
function doesTriggerExist(func) {
  var triggers = ScriptApp.getProjectTriggers();
  for (var x = 0; x < triggers.length; x++ ) {
    if (triggers[x].getHandlerFunction() == func) {
      return true;
    }
  }
  return false;
}

/**
 * Gets all available vehicle data and writes them to a Google Sheet in a nested format.
 */
// TODO:  add try catch block
function writeAllM3Data() {
  // delete previous data
  SpreadsheetApp.openById(SPREADSHEET_ID).getRange('Data-M3!A:D').deleteCells(SpreadsheetApp.Dimension.COLUMNS);
  
  // set format of columns to be written to be plain text
  SpreadsheetApp.openById(SPREADSHEET_ID).getRange('Data-M3!A:D').setNumberFormat('@');
  
  // loop through entire nested response to build input for writing all vehicle data
  var data = JSON.parse(getVehicleData(M3_VID).getContentText());
  var inputs = [];
  var row = 0;
  for (x in data.response) {
    row++;
    inputs.push({range: 'Data-M3!A' + row + ':D' + row, values: [[x,'','',Utilities.formatString('%s',data.response[x])]]});
      
    for (y in data.response[x]) {
      row++;
      inputs.push({range: 'Data-M3!B' + row + ':D' + row, values: [[y,'',Utilities.formatString('%s',data.response[x][y])]]});
      
      for (z in data.response[x][y]) {
        row++;
        inputs.push({range: 'Data-M3!C' + row + ':D' + row, values: [[z,Utilities.formatString('%s',data.response[x][y][z])]]});
      }
    }
  }
  
  // batch write data to sheet
  Sheets.Spreadsheets.Values.batchUpdate({valueInputOption: 'RAW', data: inputs}, SPREADSHEET_ID);
}

// TODO:  add try catch block
function writeAllMXData() {  
  // delete previous data
  SpreadsheetApp.openById(SPREADSHEET_ID).getRange('Data-MX!A:D').deleteCells(SpreadsheetApp.Dimension.COLUMNS);
  
  // set format of columns to be written to be plain text
  SpreadsheetApp.openById(SPREADSHEET_ID).getRange('Data-MX!A:D').setNumberFormat('@');
  
  // loop through entire nested response to build input for writing all vehicle data
  var data = JSON.parse(getVehicleData(MX_VID).getContentText());
  var inputs = [];
  var row = 0;
  for (x in data.response) {
    row++;
    inputs.push({range: 'Data-MX!A' + row + ':D' + row, values: [[x,'','',Utilities.formatString('%s',data.response[x])]]});
      
    for (y in data.response[x]) {
      row++;
      inputs.push({range: 'Data-MX!B' + row + ':D' + row, values: [[y,'',Utilities.formatString('%s',data.response[x][y])]]});
      
      for (z in data.response[x][y]) {
        row++;
        inputs.push({range: 'Data-MX!C' + row + ':D' + row, values: [[z,Utilities.formatString('%s',data.response[x][y][z])]]});
      }
    }
  }
  
  // batch write data to sheet
  Sheets.Spreadsheets.Values.batchUpdate({valueInputOption: 'RAW', data: inputs}, SPREADSHEET_ID);
}
