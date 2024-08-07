package main

import (
	"log/slog"
	"os"

	"gitlab.com/ksobrenat32/scholarships-db/code"
)

func main() {
	// Environment variables
	var (
		LOG_FILE      string
		LOG_LEVEL     string
		DATABASE_FILE string
		//DEFAULT_SHEET string
		err error
	)

	// Default values
	LOG_FILE = "scholarships.log"
	LOG_LEVEL = "INFO"
	DATABASE_FILE = "scholarships.db"
	//DEFAULT_SHEET = "APROVECHAMIENTO"
	logOpts := &slog.HandlerOptions{
		Level: slog.LevelInfo,
	}

	// Get the log file from environment variable
	if os.Getenv("LOG_FILE") != "" {
		LOG_FILE = os.Getenv("LOG_FILE")
	}

	// Get the log level from environment variable
	if os.Getenv("LOG_LEVEL") != "" {
		LOG_LEVEL = os.Getenv("LOG_LEVEL")
	}

	// Get the database file from environment variable
	if os.Getenv("DATABASE_FILE") != "" {
		DATABASE_FILE = os.Getenv("DATABASE_FILE")
	}

	// Get the default sheet from environment variable
	//if os.Getenv("DEFAULT_SHEET") != "" {
	//DEFAULT_SHEET = os.Getenv("DEFAULT_SHEET")
	//}

	// --- LOGGING ---

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
	if !code.ExistsDatabase(DATABASE_FILE) {
		err := code.CreateDatabaseFile(DATABASE_FILE)
		if err != nil {
			slog.Error(err.Error())
		}
	}

	// Get the database pointer
	//pt, err := code.GetDatabasePointer(DATABASE_FILE)
	if err != nil {
		slog.Error(err.Error())
	}

	// --- WEB SERVER ---
	code.StartWebServer()
}
