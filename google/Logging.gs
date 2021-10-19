var LOG_SPREADSHEET_ID = crypto('abcdef0123456789');

/**
 * Logs errors from try/catch blocks into a Google Sheet (I couldn't get the Stackdriver Logging/Error to work).
 */
function logError(msg) {
  // write this into an open row in logging Google Sheet
  var open_row = findOpenRow(LOG_SPREADSHEET_ID, 'error', 'A:A');
  Sheets.Spreadsheets.Values.update(
    {values: [[new Date().toLocaleTimeString() + ", " + new Date().toLocaleDateString()]]}, 
    LOG_SPREADSHEET_ID, 'error!A' + open_row, 
    {valueInputOption: "USER_ENTERED"}
  );
  Sheets.Spreadsheets.Values.update(
    {values: [[msg]]}, 
    LOG_SPREADSHEET_ID, 'error!B' + open_row, 
    {valueInputOption: "USER_ENTERED"}
  );
}

/**
 * Keeps the error log from getting too long/big; deletes any rows older than 30 days.  
 *
 * author: Michael Hwa
 */
function truncateLog() {
  // get time stamps from each log entry
  var values = Sheets.Spreadsheets.Values.get(LOG_SPREADSHEET_ID, 'error!A:A').values;
  if (!values) {return;}

  // get the date 30 days prior
  var thirty_days = new Date(Date.now() - 1000*60*60*24*30);
  
  // loop backwards through each log entry time stamp 
  for (var x = values.length; x >= 0; x--) {
    // convert time stamp to Date object
    var log_date = new Date(values[x]);
    
    // if the log item is older than 30 days, delete the row and any before it and stop execution
    if (log_date.valueOf() < thirty_days.valueOf()) {
      SpreadsheetApp.openById(LOG_SPREADSHEET_ID).getRange('error!A1:B' + (x + 1)).deleteCells(SpreadsheetApp.Dimension.ROWS);
      return;
    }
  }
}
