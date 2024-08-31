package code

import (
	"database/sql"
	"fmt"
	"log/slog"
	"os"

	_ "github.com/mattn/go-sqlite3"
)

// Database tables

type Trabajador struct {
	seccion              string
	apellido_paterno     string
	apellido_materno     string
	nombres              string
	curp                 string
	codigo_de_puesto     string
	lugar_de_adscripcion string
	telefono             string
	correo_electronico   string
}

type Becario struct {
	curp_trabajador     string
	apellido_paterno    string
	apellido_materno    string
	nombres             string
	curp                string
	fecha_de_nacimiento string
	sexo                string
}

type Historial_becario struct {
	curp_becario         string
	anio                 string
	anterior_obtuvo_beca string
	grado_cursado        string
	promedio             float64
}

// Basic database file administration operations

// GetDatabasePointer opens the database file and returns a pointer to it
func GetDatabasePointer(filepath string) (*sql.DB, error) {
	db, err := sql.Open("sqlite3", filepath)
	if err != nil {
		return nil, err
	}

	slog.Debug("Database file opened successfully")
	return db, nil
}

// ExistsDatabase checks if the database file exists
func ExistsDatabase(filePath string) bool {
	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		slog.Debug("Database file does not exist")
		return false
	}
	slog.Debug("Database file exists")
	return true
}

// CreateDatabaseFile creates the database file with the tables
func CreateDatabaseFile(filePath string) error {
	var err error
	db, err := sql.Open("sqlite3", filePath)
	slog.Info("Creating database file")

	if err != nil {
		return err
	}

	// Create workers table
	query := `
		CREATE TABLE IF NOT EXISTS 'trabajadores' (
			'id' INTEGER PRIMARY KEY,
			'seccion' TEXT NOT NULL,
			'apellido_paterno' TEXT NOT NULL,
			'apellido_materno' TEXT,
			'nombres' TEXT NOT NULL,
			'curp' TEXT NOT NULL,
			'codigo_de_puesto' TEXT NOT NULL,
			'lugar_de_adscripcion' TEXT NOT NULL,
			'telefono' TEXT,
			'correo_electronico' TEXT NOT NULL
		);
	`
	if _, err = db.Exec(query); err != nil {
		return err
	}
	slog.Info("Table 'trabajadores' created successfully")

	query = `
		CREATE TABLE IF NOT EXISTS 'becarios' (
			'id' INTEGER PRIMARY KEY,
			'curp_trabajador' TEXT NOT NULL,
			'apellido_paterno' TEXT NOT NULL,
			'apellido_materno' TEXT,
			'nombres' TEXT NOT NULL,
			'curp' TEXT NOT NULL,
			'fecha_de_nacimiento' TEXT NOT NULL,
			'sexo' TEXT NOT NULL,
			FOREIGN KEY ('curp_trabajador') REFERENCES 'trabajadores'('curp')
		);
	`
	if _, err = db.Exec(query); err != nil {
		return err
	}
	slog.Info("Table 'becarios' created successfully")

	query = `
		CREATE TABLE IF NOT EXISTS 'datos_becario' (
			'id' INTEGER PRIMARY KEY,
			'curp_becario' TEXT NOT NULL,
			'anio' TEXT NOT NULL,
			'anterior_obtuvo_beca' TEXT NOT NULL,
			'grado_cursado' TEXT NOT NULL,
			'promedio' FLOAT,
			FOREIGN KEY ('curp_becario') REFERENCES 'becarios'('curp')
		);
	`
	if _, err = db.Exec(query); err != nil {
		return err
	}
	slog.Info("Table 'datos_becario' created successfully")

	if err = db.Close(); err != nil {
		return err
	}

	slog.Info("Database file created successfully")
	return nil
}

// Database interaction

// CreateTrabajador creates a new Trabajador struct
func CreateTrabajador(seccion string, apellido_paterno string, apellido_materno string, nombres string, curp string, codigo_de_puesto string, lugar_de_adscripcion string, telefono string, correo_electronico string) Trabajador {
	return Trabajador{
		seccion:              seccion,
		apellido_paterno:     apellido_paterno,
		apellido_materno:     apellido_materno,
		nombres:              nombres,
		curp:                 curp,
		codigo_de_puesto:     codigo_de_puesto,
		lugar_de_adscripcion: lugar_de_adscripcion,
		telefono:             telefono,
		correo_electronico:   correo_electronico,
	}
}

// CreateBecario creates a new Becario struct
func CreateBecario(curp_trabajador string, apellido_paterno string, apellido_materno string, nombres string, curp string, fecha_de_nacimiento string, sexo string) Becario {
	return Becario{
		curp_trabajador:     curp_trabajador,
		apellido_paterno:    apellido_paterno,
		apellido_materno:    apellido_materno,
		nombres:             nombres,
		curp:                curp,
		fecha_de_nacimiento: fecha_de_nacimiento,
		sexo:                sexo,
	}
}

// CreateHistorial_becario creates a new Historial_becario struct
func CreateHistorial_becario(curp_becario string, anio string, anterior_obtuvo_beca string, grado_cursado string, promedio float64) Historial_becario {
	return Historial_becario{
		curp_becario:         curp_becario,
		anio:                 anio,
		anterior_obtuvo_beca: anterior_obtuvo_beca,
		grado_cursado:        grado_cursado,
		promedio:             promedio,
	}
}

// ExistsTrabajador checks if a Trabajador exists in the database
func ExistsTrabajador(db *sql.DB, curp string) (bool, error) {
	query := `
		SELECT id FROM trabajadores WHERE curp = ?
	`

	var id int
	err := db.QueryRow(query, curp).Scan(&id)

	if id != 0 {
		slog.Debug(fmt.Sprintf("Trabajador %s exists", curp))
		return true, nil
	} else if err == sql.ErrNoRows {
		slog.Debug(fmt.Sprintf("Trabajador %s does not exist", curp))
		return false, nil
	} else {
		return false, err
	}
}

// ExistsBecario checks if a Becario exists in the database
func ExistsBecario(db *sql.DB, curp string) (bool, error) {
	query := `
		SELECT id FROM becarios WHERE curp = ?
	`

	var id int
	err := db.QueryRow(query, curp).Scan(&id)

	if id != 0 {
		slog.Debug(fmt.Sprintf("Becario %s exists", curp))
		return true, nil
	} else if err == sql.ErrNoRows {
		slog.Debug(fmt.Sprintf("Becario %s does not exist", curp))
		return false, nil
	} else {
		return false, err
	}
}

// ExistsHistorial_becario checks if a Historial_becario exists in the database
func ExistsHistorial_becario(db *sql.DB, curp_becario string, anio string) (bool, error) {
	query := `
		SELECT id FROM datos_becario WHERE curp_becario = ? AND anio = ?
	`

	var id int
	err := db.QueryRow(query, curp_becario, anio).Scan(&id)

	if id != 0 {
		slog.Debug(fmt.Sprintf("Historial becario %s %s exists", curp_becario, anio))
		return true, nil
	} else if err == sql.ErrNoRows {
		slog.Debug(fmt.Sprintf("Historial becario %s %s does not exist", curp_becario, anio))
		return false, nil
	} else {
		return false, err
	}
}

// GetTrabajadorByCurp gets a Trabajador by its CURP
func GetTrabajadorByCurp(db *sql.DB, curp string) (Trabajador, error) {
	var trabajador Trabajador

	query := `
		SELECT seccion,
				apellido_paterno,
				apellido_materno,
				nombres,
				curp,
				codigo_de_puesto,
				lugar_de_adscripcion,
				telefono,
				correo_electronico
				FROM trabajadores WHERE curp = ?
	`

	err := db.QueryRow(query, curp).Scan(
		&trabajador.seccion,
		&trabajador.apellido_paterno,
		&trabajador.apellido_materno,
		&trabajador.nombres,
		&trabajador.curp,
		&trabajador.codigo_de_puesto,
		&trabajador.lugar_de_adscripcion,
		&trabajador.telefono,
		&trabajador.correo_electronico,
	)

	return trabajador, err
}

// GetTrabajadorByName gets a Trabajador by its full name
func GetTrabajadorByName(db *sql.DB, nombre_completo string) ([]Trabajador, error) {
	var (
		trabajador Trabajador
		answer     []Trabajador
	)

	query := `
		SELECT seccion,
				apellido_paterno,
				apellido_materno,
				nombres,
				curp,
				codigo_de_puesto,
				lugar_de_adscripcion,
				telefono,
				correo_electronico
		FROM trabajadores WHERE (nombres || ' ' || apellido_paterno || ' ' || apellido_materno) = '?'
	`

	rows, err := db.Query(query, nombre_completo)
	if err != nil {
		return nil, err
	}

	defer rows.Close()

	for rows.Next() {
		err = rows.Scan(
			&trabajador.seccion,
			&trabajador.apellido_paterno,
			&trabajador.apellido_materno,
			&trabajador.nombres,
			&trabajador.curp,
			&trabajador.codigo_de_puesto,
			&trabajador.lugar_de_adscripcion,
			&trabajador.telefono,
			&trabajador.correo_electronico,
		)
		if err != nil {
			return nil, err
		}
		answer = append(answer, trabajador)
	}

	return answer, err
}

// GetBecarioByCurp gets a Becario by its CURP
func GetBecarioByCurp(db *sql.DB, curp string) (Becario, error) {
	var becario Becario

	query := `
		SELECT curp_trabajador,
				apellido_paterno,
				apellido_materno,
				nombres,
				curp,
				fecha_de_nacimiento,
				sexo
				FROM becarios WHERE curp = ?
	`

	err := db.QueryRow(query, curp).Scan(
		&becario.curp_trabajador,
		&becario.apellido_paterno,
		&becario.apellido_materno,
		&becario.nombres,
		&becario.curp,
		&becario.fecha_de_nacimiento,
		&becario.sexo,
	)

	return becario, err
}

// GetHistorial_becarioByCurpAnio gets a Historial_becario by its CURP and year
func GetHistorial_becarioByCurpAnio(db *sql.DB, curp_becario string, anio string) (Historial_becario, error) {
	var historial_becario Historial_becario

	query := `
		SELECT curp_becario,
				anio,
				anterior_obtuvo_beca,
				grado_cursado,
				promedio
				FROM datos_becario WHERE curp_becario = ? AND anio = ?
	`

	err := db.QueryRow(query, curp_becario, anio).Scan(
		&historial_becario.curp_becario,
		&historial_becario.anio,
		&historial_becario.anterior_obtuvo_beca,
		&historial_becario.grado_cursado,
		&historial_becario.promedio,
	)

	return historial_becario, err
}

// GetAllListTrabajadores gets a list of all Trabajadores in the database (nombre completo, curp, correo, telefono)
func GetAllListTrabajadores(db *sql.DB) [][4]string {
	var response [][4]string
	var row [4]string

	query := `
		SELECT nombres || ' ' || apellido_paterno || ' ' || apellido_materno, curp, correo_electronico, telefono FROM trabajadores
	`

	rows, err := db.Query(query)
	if err != nil {
		slog.Error(err.Error())
		return nil
	}

	for rows.Next() {
		// Clean the row
		for i := 0; i < 4; i++ {
			row[i] = ""
		}

		err = rows.Scan(&row[0], &row[1], &row[2], &row[3])

		if err != nil {
			slog.Error(err.Error())
			return nil
		}

		// If row is not empty, append it to the response
		if row[0] != "" {
			response = append(response, row)
		}
	}

	slog.Debug("Trabajadores retrieved successfully")
	return response
}

// GetAllListBecarios gets a list of all Becarios in the database (nombre completo, curp, curp_trabajador)
func GetAllListBecarios(db *sql.DB) [][3]string {
	var response [][3]string
	var row [3]string

	query := `
		SELECT nombres || ' ' || apellido_paterno || ' ' || apellido_materno, curp, curp_trabajador FROM becarios
	`

	rows, err := db.Query(query)
	if err != nil {
		slog.Error(err.Error())
		return nil
	}

	for rows.Next() {
		err = rows.Scan(&row[0], &row[1], &row[2])
		if err != nil {
			slog.Error(err.Error())
			return nil
		}
		response = append(response, row)
	}

	slog.Debug("Becarios retrieved successfully")
	return response
}

// InsertTrabajador inserts a Trabajador into the database
func InsertTrabajador(db *sql.DB, trabajador Trabajador) error {
	query := `
		INSERT INTO trabajadores (seccion, apellido_paterno, apellido_materno, nombres, curp, codigo_de_puesto, lugar_de_adscripcion, telefono, correo_electronico)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
	`
	_, err := db.Exec(query, trabajador.seccion, trabajador.apellido_paterno, trabajador.apellido_materno, trabajador.nombres, trabajador.curp, trabajador.codigo_de_puesto, trabajador.lugar_de_adscripcion, trabajador.telefono, trabajador.correo_electronico)

	slog.Info(fmt.Sprintf("Trabajador %s inserted successfully", trabajador.curp))
	return err
}

// InsertBecario inserts a Becario into the database
func InsertBecario(db *sql.DB, becario Becario) error {
	query := `
		INSERT INTO becarios (curp_trabajador, apellido_paterno, apellido_materno, nombres, curp, fecha_de_nacimiento, sexo)
		VALUES (?, ?, ?, ?, ?, ?, ?)
	`
	_, err := db.Exec(query, becario.curp_trabajador, becario.apellido_paterno, becario.apellido_materno, becario.nombres, becario.curp, becario.fecha_de_nacimiento, becario.sexo)

	slog.Info(fmt.Sprintf("Becario %s inserted successfully", becario.curp))
	return err
}

// InsertHistorial_becario inserts a Historial_becario into the database
func InsertHistorial_becario(db *sql.DB, historial_becario Historial_becario) error {
	query := `
		INSERT INTO datos_becario (curp_becario, anio, anterior_obtuvo_beca, grado_cursado, promedio)
		VALUES (?, ?, ?, ?, ?)
	`
	_, err := db.Exec(query, historial_becario.curp_becario, historial_becario.anio, historial_becario.anterior_obtuvo_beca, historial_becario.grado_cursado, historial_becario.promedio)

	slog.Info(fmt.Sprintf("Historial becario %s inserted successfully", historial_becario.curp_becario))
	return err
}

// UpdateTrabajador updates a Trabajador in the database if necessary
func UpdateTrabajador(db *sql.DB, trabajador Trabajador) error {
	var (
		id  int
		old Trabajador
	)

	// Obtain the old values
	query := `
		SELECT id, seccion, apellido_paterno, apellido_materno, nombres, curp, codigo_de_puesto, lugar_de_adscripcion, telefono, correo_electronico FROM trabajadores WHERE curp = ?
	`
	err := db.QueryRow(query, trabajador.curp).Scan(&id, &old.seccion, &old.apellido_paterno, &old.apellido_materno, &old.nombres, &old.curp, &old.codigo_de_puesto, &old.lugar_de_adscripcion, &old.telefono, &old.correo_electronico)

	if err != nil {
		return err
	}

	if old == trabajador {
		slog.Debug(fmt.Sprintf("Trabajador %s is the same, no update needed", trabajador.curp))
		return nil
	} else {
		query = `
			UPDATE trabajadores SET seccion = ?, apellido_paterno = ?, apellido_materno = ?, nombres = ?, curp = ?, codigo_de_puesto = ?, lugar_de_adscripcion = ?, telefono = ?, correo_electronico = ? WHERE id = ?
		`

		_, err = db.Exec(query, trabajador.seccion, trabajador.apellido_paterno, trabajador.apellido_materno, trabajador.nombres, trabajador.curp, trabajador.codigo_de_puesto, trabajador.lugar_de_adscripcion, trabajador.telefono, trabajador.correo_electronico, id)

		if err != nil {
			return err
		}

		slog.Info(fmt.Sprintf("Updated trabajador %s", trabajador.curp))
		return nil
	}
}

// UpdateBecario updates a Becario in the database
func UpdateBecario(db *sql.DB, becario Becario) error {
	var (
		id  int
		old Becario
	)

	query := `
		SELECT id, curp_trabajador, apellido_paterno, apellido_materno, nombres, curp, fecha_de_nacimiento, sexo FROM becarios WHERE curp_trabajador = ? AND curp = ?
	`

	err := db.QueryRow(query, becario.curp_trabajador, becario.curp).Scan(&id, &old.curp_trabajador, &old.apellido_paterno, &old.apellido_materno, &old.nombres, &old.curp, &old.fecha_de_nacimiento, &old.sexo)
	if err != nil {
		return err
	}

	if old == becario {
		slog.Debug(fmt.Sprintf("Becario %s is the same, no update needed", becario.curp))
		return nil
	} else {
		query = `
			UPDATE becarios SET curp_trabajador = ?, apellido_paterno = ?, apellido_materno = ?, nombres = ?, curp = ?, fecha_de_nacimiento = ?, sexo = ? WHERE id = ?
		`

		_, err = db.Exec(query, becario.curp_trabajador, becario.apellido_paterno, becario.apellido_materno, becario.nombres, becario.curp, becario.fecha_de_nacimiento, becario.sexo, id)

		if err != nil {
			return err
		}
	}

	slog.Info(fmt.Sprintf("Updated becario %s", becario.curp))
	return nil
}

// UpdateHistorial_becario updates a Historial_becario in the database
func UpdateHistorial_becario(db *sql.DB, historial_becario Historial_becario) error {
	var (
		id  int
		old Historial_becario
	)

	query := `
		SELECT id, curp_becario, anio, anterior_obtuvo_beca, grado_cursado, promedio FROM datos_becario WHERE curp_becario = ? AND anio = ?
	`

	err := db.QueryRow(query, historial_becario.curp_becario, historial_becario.anio).Scan(&id, &old.curp_becario, &old.anio, &old.anterior_obtuvo_beca, &old.grado_cursado, &old.promedio)
	if err != nil {
		return err
	}

	if old == historial_becario {
		slog.Debug(fmt.Sprintf("Historial becario %s %s is the same, no update needed", historial_becario.curp_becario, historial_becario.anio))
		return nil
	} else {
		query = `
			UPDATE datos_becario SET curp_becario = ?, anio = ?, anterior_obtuvo_beca = ?, grado_cursado = ?, promedio = ? WHERE id = ?
		`

		_, err = db.Exec(query, historial_becario.curp_becario, historial_becario.anio, historial_becario.anterior_obtuvo_beca, historial_becario.grado_cursado, historial_becario.promedio, id)

		if err != nil {
			return err
		}

		slog.Info(fmt.Sprintf("Updated historial becario %s", historial_becario.curp_becario))
		return nil
	}
}
