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
