/**
 * Contains functions to read/write the vehicle's data, e.g. mileage, efficiency, etc. into a Google Sheet for tracking, 
 * analysis, and graphs.
 */
function writeM3Telemetry() { 
  try {
    // get odometer info
    var data = JSON.parse(getVehicleVehicleState(M3_VID).getContentText());
    
    var inputs = [];
    // write odometer value
    var open_row = findOpenRow(SPREADSHEET_ID, 'Telemetry','A:A');
    inputs.push({range: 'Telemetry!A' + open_row, values: [[data.response.odometer]]});
   
    // write date stamp
    inputs.push({range: 'Telemetry!B' + open_row, values: [[new Date().toLocaleDateString()]]});

    // copy mileage formulas down
    SpreadsheetApp.openById(SPREADSHEET_ID).getRange('Telemetry!C3:G3').copyTo(SpreadsheetApp.openById(SPREADSHEET_ID).getRange('Telemetry!C' + (open_row - 1) + ':G' + (open_row - 1)));

    // write data for efficiency calculation
    var starting_range = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Charger!B18').values[0]);
    var eod_range = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Charger!B10').values[0]);
    // if the starting range is less than eod range or the charging trigger doesn't exist (car isn't home), the starting range is equal to the eod range because it won't charge
    if ((starting_range < eod_range) || !(doesTriggerExist('chargeM3'))) {
      starting_range = eod_range;
    }
   
    // write the starting_range for the next day   
    inputs.push({range: 'Telemetry!H' + open_row, values: [[starting_range]]});
    inputs.push({range: 'Telemetry!I' + (open_row - 1), values: [[eod_range]]});
 
    // copy efficiency formulas down
    SpreadsheetApp.openById(SPREADSHEET_ID).getRange('Telemetry!J3:L3').copyTo(SpreadsheetApp.openById(SPREADSHEET_ID).getRange('Telemetry!J' + (open_row - 1) + ':L' + (open_row - 1)));
    
    // write temperature data into telemetry sheet
    var data = JSON.parse(getVehicleClimateState(M3_VID).getContentText());
    var inside_temp = data.response.inside_temp * 9/5 + 32;  // convert to Fahrenheit
    var outside_temp = data.response.outside_temp * 9/5 + 32;

    inputs.push({range: 'Telemetry!O' + (open_row - 1), values: [[inside_temp]]});
    inputs.push({range: 'Telemetry!P' + (open_row - 1), values: [[outside_temp]]});

    // batch write data to sheet
    Sheets.Spreadsheets.Values.batchUpdate({valueInputOption: 'USER_ENTERED', data: inputs}, SPREADSHEET_ID);
    
    // send IFTTT notification
    UrlFetchApp.fetch('https://maker.ifttt.com/trigger/write_tesla_telemetry_success/with/key/' + IFTTT_KEY + '?value1=Model 3', {});
  } catch (e) {
    logError(e);

    wakeVehicle(M3_VID);
    Utilities.sleep(WAIT_TIME);
    writeM3Telemetry();
  }
}

function writeMXTelemetry() { 
  try {
    // get odometer info
    var data = JSON.parse(getVehicleVehicleState(MX_VID).getContentText());
    
    var inputs = [];
    // write odometer value
    var open_row = findOpenRow(SPREADSHEET_ID, 'Telemetry','Q:Q');
    inputs.push({range: 'Telemetry!Q' + open_row, values: [[data.response.odometer]]});
    
    // write date stamp
    inputs.push({range: 'Telemetry!R' + open_row, values: [[new Date().toLocaleDateString()]]});
    
    // copy mileage formulas down
    SpreadsheetApp.openById(SPREADSHEET_ID).getRange('Telemetry!S3:W3').copyTo(SpreadsheetApp.openById(SPREADSHEET_ID).getRange('Telemetry!S' + (open_row - 1) + ':W' + (open_row - 1)));
    
    // write data for efficiency calculation
    var starting_range = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Charger!B17').values[0]);
    var eod_range = Number(Sheets.Spreadsheets.Values.get(SPREADSHEET_ID, 'Smart Charger!B9').values[0]);
    // if the starting range is less than eod range or the charging trigger doesn't exist (car isn't home), the starting range is equal to the eod range because it won't charge
    if ((starting_range < eod_range) || !(doesTriggerExist('chargeMX'))) {
      starting_range = eod_range;
    }

    // write the starting_range for the next day
    inputs.push({range: 'Telemetry!X' + open_row, values: [[starting_range]]});
    inputs.push({range: 'Telemetry!Y' + (open_row - 1), values: [[eod_range]]});
  
    // copy efficiency formulas down
    SpreadsheetApp.openById(SPREADSHEET_ID).getRange('Telemetry!Z3:AB3').copyTo(SpreadsheetApp.openById(SPREADSHEET_ID).getRange('Telemetry!Z' + (open_row - 1) + ':AB' + (open_row - 1)));
    
    // write temperature data into telemetry sheet
    var data = JSON.parse(getVehicleClimateState(MX_VID).getContentText());
    var inside_temp = data.response.inside_temp * 9/5 + 32;  // convert to Fahrenheit
    var outside_temp = data.response.outside_temp * 9/5 + 32;

    inputs.push({range: 'Telemetry!AE' + (open_row - 1), values: [[inside_temp]]});
    inputs.push({range: 'Telemetry!AF' + (open_row - 1), values: [[outside_temp]]});
    
    // batch write data to sheet
    Sheets.Spreadsheets.Values.batchUpdate({valueInputOption: 'USER_ENTERED', data: inputs}, SPREADSHEET_ID);
    
    // send IFTTT notification
    UrlFetchApp.fetch('https://maker.ifttt.com/trigger/write_tesla_telemetry_success/with/key/' + IFTTT_KEY + '?value1=Model X', {});
  } catch (e) {
    logError(e);

    wakeVehicle(MX_VID);
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

function getVehicleVehicleState(vid) {
  var url = 'https://owner-api.teslamotors.com/api/1/vehicles/' + vid + '/data_request/vehicle_state';
  
  var options = {
    "headers": {
      "authorization": "Bearer " + ACCESS_TOKEN
    }
  };
  
  return UrlFetchApp.fetch(url, options);
}

function getVehicleClimateState(vid) {
  var url = 'https://owner-api.teslamotors.com/api/1/vehicles/' + vid + '/data_request/climate_state';
  
  var options = {
    "headers": {
      "authorization": "Bearer " + ACCESS_TOKEN
    }
  };

  return UrlFetchApp.fetch(url, options);
}

function getVehicleData(vid) {
  var url = 'https://owner-api.teslamotors.com/api/1/vehicles/' + vid + '/vehicle_data';
  
  var options = {
    "headers": {
      "authorization": "Bearer " + ACCESS_TOKEN
    }
  };

  return UrlFetchApp.fetch(url, options);
}
