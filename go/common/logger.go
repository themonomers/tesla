package common

import (
	"fmt"
	"os"
	"strconv"
	"time"

	"google.golang.org/api/sheets/v4"
)

var LOG_SPREADSHEET_ID string
var ERROR_SHEET_ID int64

func init() {
	var err error

	var c = GetConfig()
	LOG_SPREADSHEET_ID, err = c.String("google.log_spreadsheet_id")
	logError("init(): load log spreadsheet id", err)

	e_id, err := c.Int("google.error_sheet_id")
	logError("init(): load error sheet id", err)
	ERROR_SHEET_ID = int64(e_id)
}

// Log errors into a Google Sheet.
func LogError(msg string, err error) {
	if err != nil {
		// write this into an open row in logging Google Sheet
		var open_row = strconv.Itoa(FindOpenRow(LOG_SPREADSHEET_ID, "error", "A:A"))

		var vr sheets.ValueRange
		data := []any{time.Now().Format("3:04:05 PM, 1/2/2006"), msg + " " + err.Error()}
		vr.Values = append(vr.Values, data)

		srv := GetGoogleSheetService()
		_, err = srv.Spreadsheets.Values.Update(LOG_SPREADSHEET_ID, "error!A"+open_row+":"+"B"+open_row, &vr).ValueInputOption("USER_ENTERED").Do()
		logError("LogError(): srv.Spreadsheets.Values.Update", err)

		os.Exit(1)
	}
}

// Log errors to standard output.
func logError(msg string, err error) {
	if err != nil {
		fmt.Println(time.Now().Format("2006-01-02 15:04:05") + " " + msg + " " + err.Error())
		//		os.Exit(1)
	}
}

// Keeps the error log from getting too long/big; deletes any rows older than
// 30 days.
func TruncateLog() {
	// get time stamps from each log entry
	service := GetGoogleSheetService()
	values, err := service.Spreadsheets.Values.Get(LOG_SPREADSHEET_ID, "error!A:A").Do()
	logError("TruncateLog(): service.Spreadsheets.Values.Get", err)

	if len(values.Values) == 0 {
		return
	}

	// get the date 30 days prior
	thirty_days := time.Now().Add(time.Duration(-30 * float64(time.Hour) * 24))

	// loop backwards through each log entry time stamp
	for i := len(values.Values) - 1; i >= 0; i-- {
		// convert time stamp to Date object
		log_date, err := time.Parse("3:04:05 PM, 1/2/2006", values.Values[i][0].(string))
		logError("TruncateLog(): time.Parse", err)

		// if the log item is older than 30 days, delete the row and any before it
		// and stop execution
		if log_date.Before(thirty_days) {
			delete_requests := &sheets.DeleteDimensionRequest{
				Range: &sheets.DimensionRange{
					SheetId:    ERROR_SHEET_ID,
					Dimension:  "ROWS",
					StartIndex: 0,
					EndIndex:   int64(i + 1),
				},
			}

			// add same number of rows deleted so it doesn't run out of rows
			insert_requests := &sheets.InsertDimensionRequest{
				Range: &sheets.DimensionRange{
					SheetId:    ERROR_SHEET_ID,
					Dimension:  "ROWS",
					StartIndex: int64(len(values.Values) + 1),
					EndIndex:   int64(len(values.Values) + 1 + i + 1),
				},
			}

			srv := GetGoogleSheetService()
			request := []*sheets.Request{{
				DeleteDimension: delete_requests,
			}}
			request = append(request, &sheets.Request{InsertDimension: insert_requests})

			_, err = srv.Spreadsheets.BatchUpdate(LOG_SPREADSHEET_ID, &sheets.BatchUpdateSpreadsheetRequest{Requests: request}).Do()
			logError("TruncateLog(): srv.Spreadsheets.BatchUpdate", err)

			return
		}
	}
}
