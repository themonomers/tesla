function onOpen() {
  var ui = SpreadsheetApp.getUi();
  // Or DocumentApp or FormApp.
  ui.createMenu('Custom Menu')
    .addItem('Get Products', 'getProducts')
    .addSeparator()
    .addSubMenu(ui.createMenu('Energy')
      .addItem('Get Site Status', 'getSiteStatus')
      .addItem('Get Site Live Status', 'getSiteLiveStatus')
      .addItem('Get Site Info', 'getSiteInfo')
      .addItem('Get Site History', 'getSiteHistory')
      .addItem('Get Site Time of Use History', 'getSiteTOUHistory')
      .addItem('Get Battery Status', 'getBatteryStatus')
      .addItem('Get Battery Data', 'getBatteryData'))
    .addSeparator()
    .addSubMenu(ui.createMenu('Vehicle')
      .addItem('Get Vehicle Data', 'getVehicleData')
      .addItem('Get Nearby Charging Sites', 'getVehicleChargingSites'))
    .addToUi();
}

function getProducts() {
  var token = Browser.inputBox('Enter Access Token');

  try {
    var url = 'https://owner-api.teslamotors.com/api/1/products'
    var options = {
      'headers': {
        'authorization': 'Bearer ' + token
      }
    };
    
    printOut(JSON.parse(UrlFetchApp.fetch(url, options).getContentText()));
  } catch (e) {
    SpreadsheetApp.getCurrentCell().setValue('getProducts(): ' + e);
  }
}

function getSiteStatus() {
  var token = Browser.inputBox('Enter Access Token');
  var site_id = Browser.inputBox('Enter Site ID (energy_site_id)');

  try {
    var url = 'https://owner-api.teslamotors.com/api/1/energy_sites/'
              + site_id
              + '/site_status';

    var options = {
      'headers': {
        'authorization': 'Bearer ' + token
      }
    };
    
    printOut(JSON.parse(UrlFetchApp.fetch(url, options).getContentText()));
  } catch (e) {
    SpreadsheetApp.getCurrentCell().setValue('getSiteStatus(): ' + e);
  }
}

function getSiteLiveStatus() {
  var token = Browser.inputBox('Enter Access Token');
  var site_id = Browser.inputBox('Enter Site ID (energy_site_id)');

  try {
    var url = 'https://owner-api.teslamotors.com/api/1/energy_sites/'
              + site_id
              + '/live_status';

    var options = {
      'headers': {
        'authorization': 'Bearer ' + token
      }
    };
    
    printOut(JSON.parse(UrlFetchApp.fetch(url, options).getContentText()));
  } catch (e) {
    SpreadsheetApp.getCurrentCell().setValue('getSiteLiveStatus(): ' + e);
  }
}

function getSiteInfo() {
  var token = Browser.inputBox('Enter Access Token');
  var site_id = Browser.inputBox('Enter Site ID (energy_site_id)');

  try {
    var url = 'https://owner-api.teslamotors.com/api/1/energy_sites/'
              + site_id
              + '/site_info';

    var options = {
      'headers': {
        'authorization': 'Bearer ' + token
      }
    };
    
    printOut(JSON.parse(UrlFetchApp.fetch(url, options).getContentText()));
  } catch (e) {
    SpreadsheetApp.getCurrentCell().setValue('getSiteInfo(): ' + e);
  }
}

function getSiteHistory() {
  var token = Browser.inputBox('Enter Access Token');
  var site_id = Browser.inputBox('Enter Site ID (energy_site_id)');
  var period = Browser.inputBox('Enter Period (day, week, month. year)');
  var end_date = Browser.inputBox('Enter End Date (yyyy/mm/dd)');

  var year = end_date.split('/')[0];
  var month = end_date.split('/')[1];
  var day = end_date.split('/')[2];

  var end_date = new Date(year, month - 1, day, 23, 59, 59, 999);

  try {
    var url = 'https://owner-api.teslamotors.com/api/1/energy_sites/'
              + site_id
              + '/calendar_history'
              + '?kind=energy'
              + '&period=' + period
              + '&end_date=' 
              + encodeURIComponent(Utilities.formatDate(end_date, 'Etc/GMT', 'yyyy-MM-dd\'T\'HH:mm:ss\'Z\''));

    var options = {
      'headers': {
        'authorization': 'Bearer ' + token
      }
    };
    
    printOut(JSON.parse(UrlFetchApp.fetch(url, options).getContentText()));
  } catch (e) {
    SpreadsheetApp.getCurrentCell().setValue('getSiteHistory(): ' + e);
  }
}

function getSiteTOUHistory() {
  var token = Browser.inputBox('Enter Access Token');
  var site_id = Browser.inputBox('Enter Site ID (energy_site_id)');
  var period = Browser.inputBox('Enter Period (day, week, month. year)')
  var end_date = Browser.inputBox('Enter End Date (yyyy/mm/dd)');

  var year = end_date.split('/')[0];
  var month = end_date.split('/')[1];
  var day = end_date.split('/')[2];

  var end_date = new Date(year, month - 1, day, 23, 59, 59, 999);

  try {
    var url = 'https://owner-api.teslamotors.com/api/1/energy_sites/'
              + site_id
              + '/calendar_history'
              + '?kind=time_of_use_energy'
              + '&period=' + period
              + '&end_date=' 
              + encodeURIComponent(Utilities.formatDate(end_date, 'Etc/GMT', 'yyyy-MM-dd\'T\'HH:mm:ss\'Z\''));

    var options = {
      'headers': {
        'authorization': 'Bearer ' + token
      }
    };

    printOut(JSON.parse(UrlFetchApp.fetch(url, options).getContentText()));
  } catch (e) {
    SpreadsheetApp.getCurrentCell().setValue('getSiteTOUHistory(): ' + e);
  }
}

function getBatteryStatus() {
  var token = Browser.inputBox('Enter Access Token');
  var battery_id = Browser.inputBox('Enter Battery ID (id)');

  try {
    var url = 'https://owner-api.teslamotors.com/api/1/powerwalls/'
              + battery_id
              + '/status';

    var options = {
      'headers': {
        'authorization': 'Bearer ' + token
      }
    };
    
    printOut(JSON.parse(UrlFetchApp.fetch(url, options).getContentText()));
  } catch (e) {
    SpreadsheetApp.getCurrentCell().setValue('getSiteStatus(): ' + e);
  }
}

function getBatteryData() {
  var token = Browser.inputBox('Enter Access Token');
  var battery_id = Browser.inputBox('Enter Battery ID (id)');

  try {
    var url = 'https://owner-api.teslamotors.com/api/1/powerwalls/' + battery_id;

    var options = {
      'headers': {
        'authorization': 'Bearer ' + token
      }
    };
    
    printOut(JSON.parse(UrlFetchApp.fetch(url, options).getContentText()));
  } catch (e) {
    SpreadsheetApp.getCurrentCell().setValue('getSiteStatus(): ' + e);
  }
}

function getVehicleData() {
  var token = Browser.inputBox('Enter Access Token');
  var vin = Browser.inputBox('Enter VIN');

  try {
    var url = 'https://owner-api.teslamotors.com/api/1/vehicles/' + getVehicleId(vin, token) + '/vehicle_data';
    
    var options = {
      'headers': {
        'authorization': 'Bearer ' + token
      }
    };

    printOut(JSON.parse(UrlFetchApp.fetch(url, options).getContentText()));
  } catch (e) {
    SpreadsheetApp.getCurrentCell().setValue('getVehicleData(): ' + e);
  }
}

function getVehicleChargingSites() {
  var token = Browser.inputBox('Enter Access Token');
  var vin = Browser.inputBox('Enter VIN');

  try {
    var url = 'https://owner-api.teslamotors.com/api/1/vehicles/' + getVehicleId(vin, token) + '/nearby_charging_sites';
    
    var options = {
      'headers': {
        'authorization': 'Bearer ' + token
      }
    };

    printOut(JSON.parse(UrlFetchApp.fetch(url, options).getContentText()));
  } catch (e) {
    SpreadsheetApp.getCurrentCell().setValue('getVehicleChargingSites(): ' + e);
  }
}

function getVehicleId(vin, token) {
  try {
    var url = 'https://owner-api.teslamotors.com/api/1/vehicles';
    
    var options = {
      'headers': {
        'authorization': 'Bearer ' + token
      }
    };
    var response = JSON.parse(UrlFetchApp.fetch(url, options).getContentText());
    for (var x = 0; x < response.response.length; x++) {
      if (response.response[x].vin == vin) {
        return response.response[x].id_s;
      }
    }
  } catch (e) {
    SpreadsheetApp.getCurrentCell().setValue('getVehicleId(' + vin + '): ' + e);
    Utilities.sleep(30000);    
    wakeVehicle(vin, token);
    getVehicleId(vin, token);
  }
}

function wakeVehicle(vin, token) {
  try {
    var url = 'https://owner-api.teslamotors.com/api/1/vehicles/' + getVehicleId(vin) + '/wake_up';
    var options = {
      'headers': {
        'authorization': 'Bearer ' + token
      },
      'method': 'post'
    };
    
    return UrlFetchApp.fetch(url, options);
  } catch (e) {
    SpreadsheetApp.getCurrentCell().setValue('wakeVehicle(' + vin + '): ' + e);
    Utilities.sleep(30000);    
    wakeVehicle(vin, token);
  }
}

function printOut(response) {
  var i = 0;
  for (var x in response) {
    var item_1 = response[x];
    for (key_1 in item_1) {
      SpreadsheetApp.getActiveSheet().getRange(
        SpreadsheetApp.getActiveSheet().getCurrentCell().getRow() + i, 
        SpreadsheetApp.getActiveSheet().getCurrentCell().getColumn()
      ).setValue(key_1);

      if (typeof item_1[key_1] == 'object') {
        var item_2 = item_1[key_1];
        for (key_2 in item_2) {
          i++;

          SpreadsheetApp.getActiveSheet().getRange(
            SpreadsheetApp.getActiveSheet().getCurrentCell().getRow() + i, 
            SpreadsheetApp.getActiveSheet().getCurrentCell().getColumn() + 1
          ).setValue(key_2);  

          if (typeof item_2[key_2] == 'object') {
            var item_3 = item_2[key_2];
            for (key_3 in item_3) {
              i++;

              SpreadsheetApp.getActiveSheet().getRange(
                SpreadsheetApp.getActiveSheet().getCurrentCell().getRow() + i, 
                SpreadsheetApp.getActiveSheet().getCurrentCell().getColumn() + 2
              ).setValue(key_3);

              if (typeof item_3[key_3] == 'object') {
                var item_4 = item_3[key_3];
                for (key_4 in item_4) {
                  i++;

                  SpreadsheetApp.getActiveSheet().getRange(
                    SpreadsheetApp.getActiveSheet().getCurrentCell().getRow() + i, 
                    SpreadsheetApp.getActiveSheet().getCurrentCell().getColumn() + 3
                  ).setValue(key_4);
                  SpreadsheetApp.getActiveSheet().getRange(
                    SpreadsheetApp.getActiveSheet().getCurrentCell().getRow() + i, 
                    SpreadsheetApp.getActiveSheet().getCurrentCell().getColumn() + 4
                  ).setValue(item_4[key_4]);
                }
              } else {
                SpreadsheetApp.getActiveSheet().getRange(
                  SpreadsheetApp.getActiveSheet().getCurrentCell().getRow() + i, 
                  SpreadsheetApp.getActiveSheet().getCurrentCell().getColumn() + 3
                ).setValue(item_3[key_3]);       
              }
            }
          } else {
            SpreadsheetApp.getActiveSheet().getRange(
              SpreadsheetApp.getActiveSheet().getCurrentCell().getRow() + i, 
              SpreadsheetApp.getActiveSheet().getCurrentCell().getColumn() + 2
            ).setValue(item_2[key_2]);  
          }
        }
      } else {
        SpreadsheetApp.getActiveSheet().getRange(
          SpreadsheetApp.getActiveSheet().getCurrentCell().getRow() + i, 
          SpreadsheetApp.getActiveSheet().getCurrentCell().getColumn() + 1
        ).setValue(item_1[key_1]);
      }

      i++;
    }
  }
}


