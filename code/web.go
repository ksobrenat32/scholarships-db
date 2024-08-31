package code

import (
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"os"
	"text/template"
	"time"
)

// Compile templates on start of the application
var templates = template.Must(template.ParseFiles(GetFilesDirectory()+"/index.html", GetFilesDirectory()+"/upload.html", GetFilesDirectory()+"/list.html"))

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
	dst, err := os.CreateTemp(GetUploadDirectory(), fmt.Sprintf("%d-%d-%d", currentTime.Year(), currentTime.Month(), currentTime.Day())+"-*.xlsx")
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

func serveScript(w http.ResponseWriter, r *http.Request) {
	http.ServeFile(w, r, GetFilesDirectory()+"/script.js")
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

func listHandler(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case "GET":
		display(w, "list", nil)
		slog.Debug("GET /list")
	}
}

// Returns a json with the list of trabajadores
func listTrabajadoresHandler(w http.ResponseWriter, r *http.Request) {
	ptr, err := GetDatabasePointer(GetDatabaseFile())
	if err != nil {
		slog.Error(err.Error())
		return
	}

	var list [][4]string = GetAllListTrabajadores(ptr)
	switch r.Method {
	case "GET":
		slog.Debug("GET /list/trabajadores")
		w.Header().Set("Content-Type", "application/json")

		// Convert to json
		json, err := json.Marshal(list)
		if err != nil {
			slog.Error(err.Error())
			return
		}

		// Send the json
		w.Write(json)
	}
}

// Returns a json with the list of becarios
func listBecariosHandler(w http.ResponseWriter, r *http.Request) {
	ptr, err := GetDatabasePointer(GetDatabaseFile())
	if err != nil {
		slog.Error(err.Error())
		return
	}

	var list [][3]string = GetAllListBecarios(ptr)
	switch r.Method {
	case "GET":
		slog.Debug("GET /list/becarios")
		w.Header().Set("Content-Type", "application/json")

		// Convert to json
		json, err := json.Marshal(list)
		if err != nil {
			slog.Error(err.Error())
			return
		}

		// Send the json
		w.Write(json)
	}
}

func StartWebServer() {
	http.HandleFunc("/", indexHandler)
	http.HandleFunc("/script.js", serveScript)
	http.HandleFunc("/upload", uploadHandler)
	http.HandleFunc("/list", listHandler)
	http.HandleFunc("/list/trabajadores", listTrabajadoresHandler)
	http.HandleFunc("/list/becarios", listBecariosHandler)
	slog.Info("Starting Web Server on :" + GetPort())
	http.ListenAndServe(":"+GetPort(), nil)
}
