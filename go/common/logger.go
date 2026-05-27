package common

import (
	"context"
	"fmt"
	"io"
	"log"
	"log/slog"
	"os"
	"sync"
)

// Setup initializes a file-backed logger and sets it as the system default.
// It returns a cleanup function to close the log file gracefully when the app exits.
func InitLogger() (func(), error) {
	// Open or create the log file with read-write, append, and create permissions
	file, err := os.OpenFile("./logs/tesla.log", os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
	if err != nil {
		log.Fatalf("Failed to open log file: %v", err)
	}

	// Initialize our custom handler with a minimum level filter
	handler := NewCustomHandler(file, slog.HandlerOptions{
		Level: slog.LevelInfo,
	})

	// Set the custom logger as the global application default
	logger := slog.New(handler)
	slog.SetDefault(logger)

	// Return a closure to execute when closing down the main routine
	cleanup := func() {
		_ = file.Close()
	}

	return cleanup, nil
}

// CustomHandler implements the slog.Handler interface for raw formatting
type CustomHandler struct {
	w    io.Writer
	mu   *sync.Mutex
	opts slog.HandlerOptions
}

func NewCustomHandler(w io.Writer, opts slog.HandlerOptions) *CustomHandler {
	return &CustomHandler{
		w:    w,
		mu:   &sync.Mutex{},
		opts: opts,
	}
}

// Enabled checks if the record's level meets the minimum configured level
func (h *CustomHandler) Enabled(_ context.Context, level slog.Level) bool {
	minLevel := h.opts.Level
	if minLevel == nil {
		minLevel = slog.LevelInfo
	}
	return level >= minLevel.Level()
}

// Handle formats the record without keys, equals signs, or quotes
func (h *CustomHandler) Handle(_ context.Context, r slog.Record) error {
	h.mu.Lock()
	defer h.mu.Unlock()

	line := fmt.Sprintf("%s %s %s\n", r.Time.Format("2006-01-02 15:04:05"), r.Level.String(), r.Message)

	_, err := io.WriteString(h.w, line)
	return err
}

// WithAttrs and WithGroup are required to implement the interface
func (h *CustomHandler) WithAttrs(attrs []slog.Attr) slog.Handler { return h }
func (h *CustomHandler) WithGroup(name string) slog.Handler       { return h }

/*
// Keeps the log from getting too long/big; deletes any rows older than
// 30 days.
func TruncateLog() {
	// get time stamps from each log entry
	service := GetGoogleSheetService()
	values, err := service.Spreadsheets.Values.Get(LOG_SPREADSHEET_ID, "log!B2:B").Do()
	LogError("TruncateLog(): service.Spreadsheets.Values.Get", err)

	if len(values.Values) == 0 {
		return
	}

	// get the date 30 days prior
	thirty_days := time.Now().Add(time.Duration(-30 * float64(time.Hour) * 24))

	// loop backwards through each log entry time stamp
	for i := len(values.Values) - 1; i >= 0; i-- {
		// convert time stamp to Date object
		log_date, err := time.Parse("2006-01-02 15:04:05", values.Values[i][0].(string))
		LogError("TruncateLog(): time.Parse", err)

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
			LogError("TruncateLog(): srv.Spreadsheets.BatchUpdate", err)

			return
		}
	}
}*/
