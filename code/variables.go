package code

import "os"

// GetLogFile
func GetLogFile() string {
	LOG_FILE := "scholarships.log"
	if os.Getenv("LOG_FILE") != "" {
		LOG_FILE = os.Getenv("LOG_FILE")
	}
	return LOG_FILE
}

// GetLogLevel
func GetLogLevel() string {
	LOG_LEVEL := "INFO"
	if os.Getenv("LOG_LEVEL") != "" {
		LOG_LEVEL = os.Getenv("LOG_LEVEL")
	}
	return LOG_LEVEL
}

// GetDatabaseFile
func GetDatabaseFile() string {
	DATABASE_FILE := "scholarships.db"
	if os.Getenv("DATABASE_FILE") != "" {
		DATABASE_FILE = os.Getenv("DATABASE_FILE")
	}
	return DATABASE_FILE
}

// GetDefaultSheet
func GetDefaultSheet() string {
	DEFAULT_SHEET := "APROVECHAMIENTO"
	if os.Getenv("DEFAULT_SHEET") != "" {
		DEFAULT_SHEET = os.Getenv("DEFAULT_SHEET")
	}
	return DEFAULT_SHEET
}
