package code

import (
	"database/sql"
	"fmt"
	"log/slog"
	"strconv"
	"time"

	"github.com/xuri/excelize/v2"
)

// Spreadsheet interaction

func DebugPrintSpreadSheet(filepath string) error {
	print("Reading file: ", filepath, "\n")
	file, err := excelize.OpenFile(filepath)
	if err != nil {
		return err
	}
	defer file.Close()

	// Print row number
	rows, err := file.GetRows("APROVECHAMIENTO")
	if err != nil {
		return err
	}

	cnt := 0

	for _, row := range rows {
		// If row does not have CURP, skip
		if row[5] == "" {
			continue
		}
		cnt++
		for _, cell := range row {
			print(cell, "\t")
		}
		print("\n")
	}
	print("Rows: ", cnt, "\n")
	print("Columns: ", len(rows[0]), "\n")

	return nil
}

func ReadNewSpreadSheet(db *sql.DB, filepath string, sheet string) error {
	file, err := excelize.OpenFile(filepath)
	if err != nil {
		return err
	}
	defer file.Close()
	slog.Info(fmt.Sprintf("Reading file: %s", filepath))

	var (
		trabajador_row        Trabajador
		becario_row           Becario
		historial_becario_row Historial_becario
	)

	rows, err := file.GetRows(sheet)
	if err != nil {
		return err
	}

	for _, row := range rows {
		// If header, skip
		if row[0] == "NO" {
			continue
		}
		// If row does not have CURP, skip
		if row[5] == "" {
			continue
		}
		slog.Debug(fmt.Sprintf("Reading CURP: %s", row[5]))
		if len(row) < 19 {
			slog.Debug("Row has less than 19 columns, it may be missing data")
		}

		// While row is less than 19, append empty strings
		for len(row) < 19 {
			row = append(row, "")
		}

		trabajador_row = Trabajador{
			seccion:              row[1],
			apellido_paterno:     row[2],
			apellido_materno:     row[3],
			nombres:              row[4],
			curp:                 row[5],
			codigo_de_puesto:     row[6],
			lugar_de_adscripcion: row[7],
			telefono:             row[18],
			correo_electronico:   row[8],
		}

		becario_row = Becario{
			curp_trabajador:     row[5],
			apellido_paterno:    row[9],
			apellido_materno:    row[10],
			nombres:             row[11],
			curp:                row[12],
			fecha_de_nacimiento: row[13],
			sexo:                row[14],
		}

		tmp_promedio := 0.0
		if row[17] != "" {
			tmp_promedio, err = strconv.ParseFloat(row[17], 64)
		}
		if err != nil {
			return err

		}

		historial_becario_row = Historial_becario{
			curp_becario:         row[12],
			anio:                 strconv.Itoa(time.Now().Year()),
			anterior_obtuvo_beca: row[15],
			grado_cursado:        row[16],
			promedio:             tmp_promedio,
		}

		historial_becario_row.promedio = tmp_promedio

		// If trabajador exists, verify if different for update
		if c, err := ExistsTrabajador(db, trabajador_row.curp); c {
			if err != nil {
				return err
			}
			slog.Debug(fmt.Sprintf("Trabajador %s exists", trabajador_row.curp))

			err = UpdateTrabajador(db, trabajador_row)
			if err != nil {
				return err
			}
		} else {
			if err != nil {
				return err
			}
			slog.Info(fmt.Sprintf("Trabajador %s does not exist, inserting", trabajador_row.curp))

			err = InsertTrabajador(db, trabajador_row)
			if err != nil {
				return err
			}
		}

		// If no becario CURP, skip
		if becario_row.curp == "" {
			continue
		}

		// If becario exists, verify if different for update
		if c, err := ExistsBecario(db, becario_row.curp); c {
			if err != nil {
				return err
			}
			slog.Debug(fmt.Sprintf("Becario %s exists", becario_row.curp))

			err = UpdateBecario(db, becario_row)
			if err != nil {
				return err
			}
		} else {
			if err != nil {
				return err
			}
			slog.Info(fmt.Sprintf("Becario %s does not exist, inserting", becario_row.curp))

			err = InsertBecario(db, becario_row)
			if err != nil {
				return err
			}
		}

		// If historial_becario exists, verify if different for update
		if c, err := ExistsHistorial_becario(db, historial_becario_row.curp_becario, historial_becario_row.anio); c {
			if err != nil {
				return err
			}
			slog.Debug(fmt.Sprintf("Historial becario %s %s exists", historial_becario_row.curp_becario, historial_becario_row.anio))

			err = UpdateHistorial_becario(db, historial_becario_row)
			if err != nil {
				return err
			}
		} else {
			if err != nil {
				return err
			}
			slog.Info(fmt.Sprintf("Historial becario %s %s does not exist, inserting", historial_becario_row.curp_becario, historial_becario_row.anio))

			err = InsertHistorial_becario(db, historial_becario_row)
			if err != nil {
				return err
			}
		}
	}

	slog.Info("Spreadsheet read successfully")
	return nil
}
