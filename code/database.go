package code

import (
	"database/sql"
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

func GetDatabasePointer(filepath string) (*sql.DB, error) {
	db, err := sql.Open("sqlite3", filepath)
	if err != nil {
		return nil, err
	}
	return db, nil
}

func ExistsDatabase(filePath string) bool {
	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		return false
	}
	return true
}

func CreateDatabaseFile(filePath string) error {
	var err error
	db, err := sql.Open("sqlite3", filePath)

	if err != nil {
		return err
	}

	// Create workers table
	query := `
		CREATE TABLE IF NOT EXISTS 'trabajadores' (
			'id' INTEGER PRIMARY KEY,
			'seccion' TEXT NOT NULL,
			'unidad' TEXT NOT NULL,
			'apellido_paterno' TEXT NOT NULL,
			'apellido_materno' TEXT,
			'nombre' TEXT NOT NULL,
			'curp' TEXT NOT NULL,
			'codigo_de_puesto' TEXT NOT NULL,
			'lugar_de_adscripcion' TEXT NOT NULL,
			'telefono' TEXT NOT NULL,
			'correo_electronico' TEXT NOT NULL
		);
	`
	if _, err = db.Exec(query); err != nil {
		return err
	}

	query = `
		CREATE TABLE IF NOT EXISTS 'becarios' (
			'id' INTEGER PRIMARY KEY,
			'curp_trabajador' TEXT NOT NULL,
			'apellido_paterno' TEXT NOT NULL,
			'apellido_materno' TEXT,
			'nombre' TEXT NOT NULL,
			'curp' TEXT NOT NULL,
			'fecha_de_nacimiento' TEXT NOT NULL,
			'sexo' TEXT NOT NULL,
			FOREIGN KEY ('curp_trabajador') REFERENCES 'trabajadores'('curp')
		);
	`
	if _, err = db.Exec(query); err != nil {
		return err
	}

	query = `
		CREATE TABLE IF NOT EXISTS 'datos_becario' (
			'id' INTEGER PRIMARY KEY,
			'curp_becario' TEXT NOT NULL,
			'anio' TEXT NOT NULL,
			'anterior_obtuvo_beca' TEXT NOT NULL,
			'grado_cursado' TEXT NOT NULL,
			'promedio' FLOAT NOT NULL,
			FOREIGN KEY ('curp_becario') REFERENCES 'becarios'('curp')
		);
	`
	if _, err = db.Exec(query); err != nil {
		return err
	}

	if err = db.Close(); err != nil {
		return err
	}

	return nil
}

func DeleteFile(filePath string) error {
	if err := os.Remove(filePath); err != nil {
		return err
	}
	return nil
}

// Database interaction

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

func CreateHistorial_becario(curp_becario string, anio string, anterior_obtuvo_beca string, grado_cursado string, promedio float64) Historial_becario {
	return Historial_becario{
		curp_becario:         curp_becario,
		anio:                 anio,
		anterior_obtuvo_beca: anterior_obtuvo_beca,
		grado_cursado:        grado_cursado,
		promedio:             promedio,
	}
}

func ExistsTrabajador(db *sql.DB, curp string) (bool, error) {
	query := `
		SELECT * FROM trabajadores WHERE curp = ?
	`
	err := db.QueryRow(query, curp).Scan()

	if err != nil {
		return false, err
	} else if err == sql.ErrNoRows {
		return false, nil
	} else {
		return true, nil
	}
}

func ExistsBecario(db *sql.DB, curp string) (bool, error) {
	query := `
		SELECT * FROM becarios WHERE curp = ?
	`
	err := db.QueryRow(query, curp).Scan()

	if err != nil {
		return false, err
	} else if err == sql.ErrNoRows {
		return false, nil
	} else {
		return true, nil
	}
}

func ExistsHistorial_becario(db *sql.DB, curp_becario string, anio string) (bool, error) {
	query := `
		SELECT * FROM datos_becario WHERE curp_becario = ? AND anio = ?
	`
	err := db.QueryRow(query, curp_becario, anio).Scan()

	if err != nil {
		return false, err
	} else if err == sql.ErrNoRows {
		return false, nil
	} else {
		return true, nil
	}
}

func GetTrabajadorByCurp(db *sql.DB, curp string) (Trabajador, error) {
	var trabajador Trabajador

	query := `
		SELECT * FROM trabajadores WHERE curp = ?
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

func GetTrabajadorByName(db *sql.DB, nombre_completo string) ([]Trabajador, error) {
	var (
		trabajador Trabajador
		answer     []Trabajador
	)

	query := `
		SELECT * FROM trabajadores WHERE (nombres || ' ' || apellido_paterno || ' ' || apellido_materno) = ?
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

func GetBecarioByCurp(db *sql.DB, curp string) (Becario, error) {
	var becario Becario

	query := `
		SELECT * FROM becarios WHERE curp = ?
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

func GetHistorial_becarioByCurpAnio(db *sql.DB, curp_becario string, anio string) (Historial_becario, error) {
	var historial_becario Historial_becario

	query := `
		SELECT * FROM datos_becario WHERE curp_becario = ? AND anio = ?
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

func InsertTrabajador(db *sql.DB, trabajador Trabajador) error {
	query := `
		INSERT INTO trabajadores (seccion, apellido_paterno, apellido_materno, nombres, curp, codigo_de_puesto, lugar_de_adscripcion, telefono, correo_electronico)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
	`
	_, err := db.Exec(query, trabajador.seccion, trabajador.apellido_paterno, trabajador.apellido_materno, trabajador.nombres, trabajador.curp, trabajador.codigo_de_puesto, trabajador.lugar_de_adscripcion, trabajador.telefono, trabajador.correo_electronico)
	return err
}

func InsertBecario(db *sql.DB, becario Becario) error {
	query := `
		INSERT INTO becarios (curp_trabajador, apellido_paterno, apellido_materno, nombres, curp, fecha_de_nacimiento, sexo)
		VALUES (?, ?, ?, ?, ?, ?, ?)
	`
	_, err := db.Exec(query, becario.curp_trabajador, becario.apellido_paterno, becario.apellido_materno, becario.nombres, becario.curp, becario.fecha_de_nacimiento, becario.sexo)
	return err
}

func InsertHistorial_becario(db *sql.DB, historial_becario Historial_becario) error {
	query := `
		INSERT INTO datos_becario (curp_becario, anio, anterior_obtuvo_beca, grado_cursado, promedio)
		VALUES (?, ?, ?, ?, ?)
	`
	_, err := db.Exec(query, historial_becario.curp_becario, historial_becario.anio, historial_becario.anterior_obtuvo_beca, historial_becario.grado_cursado, historial_becario.promedio)
	return err
}

func UpdateTrabajador(db *sql.DB, trabajador_original Trabajador, trabajador_nuevo Trabajador) error {
	var (
		id int
	)

	query := `
		SELECT id FROM trabajadores WHERE seccion = ? AND apellido_paterno = ? AND apellido_materno = ? AND nombres = ? AND curp = ? AND codigo_de_puesto = ? AND lugar_de_adscripcion = ? AND telefono = ? AND correo_electronico = ?
	`

	err := db.QueryRow(query, trabajador_original.seccion, trabajador_original.apellido_paterno, trabajador_original.apellido_materno, trabajador_original.nombres, trabajador_original.curp, trabajador_original.codigo_de_puesto, trabajador_original.lugar_de_adscripcion, trabajador_original.telefono, trabajador_original.correo_electronico).Scan(&id)

	if err != nil {
		return err
	}

	query = `
		UPDATE trabajadores SET seccion = ?, apellido_paterno = ?, apellido_materno = ?, nombres = ?, curp = ?, codigo_de_puesto = ?, lugar_de_adscripcion = ?, telefono = ?, correo_electronico = ? WHERE id = ?
	`

	_, err = db.Exec(query, trabajador_nuevo.seccion, trabajador_nuevo.apellido_paterno, trabajador_nuevo.apellido_materno, trabajador_nuevo.nombres, trabajador_nuevo.curp, trabajador_nuevo.codigo_de_puesto, trabajador_nuevo.lugar_de_adscripcion, trabajador_nuevo.telefono, trabajador_nuevo.correo_electronico, id)

	if err != nil {
		return err
	}

	return nil
}

func UpdateBecario(db *sql.DB, becario_original Becario, becario_nuevo Becario) error {
	var (
		id int
	)

	query := `
		SELECT id FROM becarios WHERE curp_trabajador = ? AND apellido_paterno = ? AND apellido_materno = ? AND nombres = ? AND curp = ? AND fecha_de_nacimiento = ? AND sexo = ?
	`

	err := db.QueryRow(query, becario_original.curp_trabajador, becario_original.apellido_paterno, becario_original.apellido_materno, becario_original.nombres, becario_original.curp, becario_original.fecha_de_nacimiento, becario_original.sexo).Scan(&id)

	if err != nil {
		return err
	}

	query = `
		UPDATE becarios SET curp_trabajador = ?, apellido_paterno = ?, apellido_materno = ?, nombres = ?, curp = ?, fecha_de_nacimiento = ?, sexo = ? WHERE id = ?
	`

	_, err = db.Exec(query, becario_nuevo.curp_trabajador, becario_nuevo.apellido_paterno, becario_nuevo.apellido_materno, becario_nuevo.nombres, becario_nuevo.curp, becario_nuevo.fecha_de_nacimiento, becario_nuevo.sexo, id)

	if err != nil {
		return err
	}

	return nil
}

func UpdateHistorial_becario(db *sql.DB, historial_becario_original Historial_becario, historial_becario_nuevo Historial_becario) error {
	var (
		id int
	)

	query := `
		SELECT id FROM datos_becario WHERE curp_becario = ? AND anio = ? AND anterior_obtuvo_beca = ? AND grado_cursado = ? AND promedio = ?
	`

	err := db.QueryRow(query, historial_becario_original.curp_becario, historial_becario_original.anio, historial_becario_original.anterior_obtuvo_beca, historial_becario_original.grado_cursado, historial_becario_original.promedio).Scan(&id)

	if err != nil {
		return err
	}

	query = `
		UPDATE datos_becario SET curp_becario = ?, anio = ?, anterior_obtuvo_beca = ?, grado_cursado = ?, promedio = ? WHERE id = ?
	`

	_, err = db.Exec(query, historial_becario_nuevo.curp_becario, historial_becario_nuevo.anio, historial_becario_nuevo.anterior_obtuvo_beca, historial_becario_nuevo.grado_cursado, historial_becario_nuevo.promedio, id)

	if err != nil {
		return err
	}

	return nil
}
