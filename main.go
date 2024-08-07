package main

import (
	"log/slog"
	"os"

	"gitlab.com/ksobrenat32/scholarships-db/code"
)

func main() {
	// --- LOGGING ---
	LOG_FILE := code.GetLogFile()
	LOG_LEVEL := code.GetLogLevel()

	logOpts := &slog.HandlerOptions{
		Level: slog.LevelInfo,
	}

	switch LOG_LEVEL {
	case "DEBUG":
		logOpts = &slog.HandlerOptions{
			Level: slog.LevelDebug,
		}
	case "INFO":
		logOpts = &slog.HandlerOptions{
			Level: slog.LevelInfo,
		}
	case "WARNING":
		logOpts = &slog.HandlerOptions{
			Level: slog.LevelWarn,
		}
	case "ERROR":
		logOpts = &slog.HandlerOptions{
			Level: slog.LevelError,
		}
	}

	// Open the log file
	logFile, err := os.OpenFile(LOG_FILE, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		slog.Error(err.Error())
	}
	defer logFile.Close()

	// Set the default logger to the log file
	logger := slog.New(slog.NewTextHandler(logFile, logOpts))
	slog.SetDefault(logger)

	// --- DATABASE ---

	// Check if the database file exists, if not, create it
	if !code.ExistsDatabase(code.GetDatabaseFile()) {
		err := code.CreateDatabaseFile(code.GetDatabaseFile())
		if err != nil {
			slog.Error(err.Error())
		}
	}

	// --- WEB SERVER ---
	code.StartWebServer()
}
