var DELETE_THRESHOLD = 30;  // days


/**
 * Keeps the email sent folder from being overloaded with 
 * notifications; deletes any notification emails older than 
 * a specified number of days.  
 *
 * author: mjhwa@yahoo.com
 */
function truncateEmail() {
  var queries = [
    'in:sent subject:"Model X"', 
    'in:sent subject:"Model 3"', 
  ];

  for (var i = 0; i < queries.length; i++) {
    truncateEmailExecute(queries[i]);
  }
}


function truncateEmailExecute(query) {
  // get the date for the threshold (days prior)
  var delete_date = new Date(Date.now() - 1000*60*60*24*DELETE_THRESHOLD);
//  Logger.log('threshold: ' + delete_date);
  
  var messages = GmailApp.getMessagesForThreads(GmailApp.search(query));
  var email_date = '';
  for (var x = 0; x < messages.length; x++) {
    for (var y = 0; y < messages[x].length; y++) {
//      Logger.log(messages[x][y].getDate().toLocaleDateString() + ' ' + messages[x][y].getDate().toLocaleTimeString() + ' ' + messages[x][y].getSubject());
      email_date = new Date(messages[x][y].getDate());
      if (email_date.valueOf() < delete_date.valueOf()) {
//        Logger.log('delete: ' + messages[x][y].getDate().toLocaleDateString() + ' ' + messages[x][y].getDate().toLocaleTimeString() + ' ' + messages[x][y].getSubject());
        messages[x][y].moveToTrash();
      }
    }
  }
}