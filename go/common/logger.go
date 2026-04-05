package common

import (
	"fmt"
	"os"
	"strconv"
	"time"

	"google.golang.org/api/sheets/v4"
)

var LOG_SPREADSHEET_ID string
var LOG_SHEET_ID int64
var INFO = "INFO"
var WARN = "WARN"
var ERROR = "ERROR"

func init() {
	var err error

	var c = GetConfig()
	LOG_SPREADSHEET_ID, err = c.String("google.log_spreadsheet_id")
	logErrorStdOut("init(): load log spreadsheet id", err)

	e_id, err := c.Int("google.log_sheet_id")
	logErrorStdOut("init(): load log sheet id", err)
	LOG_SHEET_ID = int64(e_id)
}

// Logs information into a Google Sheet.
func log(level string, msg string) {
	// write this into an open row in logging Google Sheet
	var open_row = strconv.Itoa(FindOpenRow(LOG_SPREADSHEET_ID, "log", "A:A"))

	var vr sheets.ValueRange
	data := []any{level, time.Now().Format("2006-01-02 15:04:05"), msg}
	vr.Values = append(vr.Values, data)
	srv := GetGoogleSheetService()
	_, err := srv.Spreadsheets.Values.Update(LOG_SPREADSHEET_ID, "log!A"+open_row+":"+"C"+open_row, &vr).ValueInputOption("USER_ENTERED").Do()
	logErrorStdOut("log(): srv.Spreadsheets.Values.Update", err)

	if level == ERROR {
		os.Exit(1)
	}
}

// Log errors to standard output.
func logErrorStdOut(msg string, err error) {
	if err != nil {
		fmt.Println("[ERROR] " + time.Now().Format("2006-01-02 15:04:05") + " " + msg + " " + err.Error())
		//		os.Exit(1)
	}
}

func LogInfo(msg string) {
	log(INFO, msg)
}

func LogWarn(msg string) {
	log(WARN, msg)
}

func LogError(msg string, err error) {
	log(ERROR, msg+" "+err.Error())
}

// Keeps the log from getting too long/big; deletes any rows older than
// 30 days.
func TruncateLog() {
	// get time stamps from each log entry
	service := GetGoogleSheetService()
	values, err := service.Spreadsheets.Values.Get(LOG_SPREADSHEET_ID, "log!B2:B").Do()
	logErrorStdOut("TruncateLog(): service.Spreadsheets.Values.Get", err)

	if len(values.Values) == 0 {
		return
	}

	// get the date 30 days prior
	thirty_days := time.Now().Add(time.Duration(-30 * float64(time.Hour) * 24))

	// loop backwards through each log entry time stamp
	for i := len(values.Values) - 1; i >= 0; i-- {
		// convert time stamp to Date object
		log_date, err := time.Parse("2006-01-02 15:04:05", values.Values[i][0].(string))
		logErrorStdOut("TruncateLog(): time.Parse", err)

		// if the log item is older than 30 days, delete the row and any before it
		// and stop execution
		if log_date.Before(thirty_days) {
			delete_requests := &sheets.DeleteDimensionRequest{
				Range: &sheets.DimensionRange{
					SheetId:    LOG_SHEET_ID,
					Dimension:  "ROWS",
					StartIndex: 1,
					EndIndex:   int64(i + 2),
				},
			}

			// add same number of rows deleted so it doesn't run out of rows
			insert_requests := &sheets.InsertDimensionRequest{
				Range: &sheets.DimensionRange{
					SheetId:    LOG_SHEET_ID,
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
			logErrorStdOut("TruncateLog(): srv.Spreadsheets.BatchUpdate", err)

			return
		}
	}
}
