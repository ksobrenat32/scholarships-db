package code

import (
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"os"
	"text/template"
	"time"
)

// Compile templates on start of the application
var templates = template.Must(template.ParseFiles("files/index.html", "files/upload.html"))

// Display the named template
func display(w http.ResponseWriter, page string, data interface{}) {
	templates.ExecuteTemplate(w, page+".html", data)
	slog.Debug(fmt.Sprintf("Displaying %s", page))
}

// Upload file function
func uploadFile(w http.ResponseWriter, r *http.Request) {
	// Maximum upload of 512MB files
	r.ParseMultipartForm(512 << 20)

	// Get handler for filename, size and headers
	file, handler, err := r.FormFile("excel-file")
	if err != nil {
		slog.Error(fmt.Sprintf("Error Retrieving the File: %s", err))
		return
	}
	defer file.Close()

	slog.Info(fmt.Sprintf("Uploaded File: %+v", handler.Filename))
	slog.Info(fmt.Sprintf("File Size: %+v", handler.Size))

	// Create file on the server
	currentTime := time.Now()
	dst, err := os.CreateTemp("uploads", fmt.Sprintf("%d-%d-%d", currentTime.Year(), currentTime.Month(), currentTime.Day())+"-*.xlsx")
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	slog.Debug(fmt.Sprintf("Created File: %s", dst.Name()))
	defer dst.Close()

	// Copy the uploaded file to the created file on the filesystem
	if _, err := io.Copy(dst, file); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	slog.Info(fmt.Sprintf("Successfully Uploaded File: %s to %s", handler.Filename, dst.Name()))

	ptr, err := GetDatabasePointer(GetDatabaseFile())
	if err != nil {
		slog.Error(err.Error())
		return
	}

	err = ReadNewSpreadSheet(ptr, dst.Name(), GetDefaultSheet())
	if err != nil {
		slog.Error("Error reading spreadsheet")
		slog.Error(err.Error())
	}
}

func indexHandler(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case "GET":
		display(w, "index", nil)
		slog.Debug("GET /")
	}
}

// Upload handler depending on the HTTP method
func uploadHandler(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case "GET":
		display(w, "upload", nil)
		slog.Debug("GET /upload")
	case "POST":
		uploadFile(w, r)
		display(w, "upload", nil)
		slog.Debug("POST /upload")
	}
}

func StartWebServer() {
	http.HandleFunc("/", indexHandler)
	http.HandleFunc("/upload", uploadHandler)
	slog.Info("Starting Web Server on :8080")
	http.ListenAndServe(":8080", nil)
}
