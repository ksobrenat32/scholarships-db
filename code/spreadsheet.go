package code

import (
	"database/sql"
	"strconv"
	"time"

	"github.com/xuri/excelize/v2"
)

// Spreadsheet interaction

func ReadNewSpreadSheet(db *sql.DB, filepath string) error {
	file, err := excelize.OpenFile(filepath)
	if err != nil {
		return err
	}
	defer file.Close()

	var (
		trabajador_row             Trabajador
		trabajador_existing        Trabajador
		becario_row                Becario
		becario_existing           Becario
		historial_becario_row      Historial_becario
		historial_becario_existing Historial_becario
	)

	rows, err := file.GetRows("APROVECHAMIENTO")
	if err != nil {
		return err
	}

	for _, row := range rows {
		trabajador_row = Trabajador{
			seccion:              row[1],
			apellido_paterno:     row[2],
			apellido_materno:     row[3],
			nombres:              row[4],
			curp:                 row[5],
			codigo_de_puesto:     row[6],
			lugar_de_adscripcion: row[7],
			telefono:             row[8],
			correo_electronico:   row[18],
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

		historial_becario_row = Historial_becario{
			curp_becario:         row[12],
			anio:                 strconv.Itoa(time.Now().Year()),
			anterior_obtuvo_beca: row[15],
			grado_cursado:        row[16],
		}

		historial_becario_row.promedio, err = strconv.ParseFloat(row[17], 64)
		if err != nil {
			return err
		}

		// If trabajador exists, verify if different for update
		if c, err := ExistsTrabajador(db, trabajador_row.curp); c {
			if err != nil {
				return err
			}

			trabajador_existing, err = GetTrabajadorByCurp(db, trabajador_row.curp)
			if err != nil {
				return err
			}

			if UnifyText(trabajador_row.seccion) != UnifyText(trabajador_existing.seccion) || UnifyText(trabajador_row.apellido_paterno) != UnifyText(trabajador_existing.apellido_paterno) || UnifyText(trabajador_row.apellido_materno) != UnifyText(trabajador_existing.apellido_materno) || UnifyText(trabajador_row.nombres) != UnifyText(trabajador_existing.nombres) || UnifyText(trabajador_row.codigo_de_puesto) != UnifyText(trabajador_existing.codigo_de_puesto) || UnifyText(trabajador_row.lugar_de_adscripcion) != UnifyText(trabajador_existing.lugar_de_adscripcion) || UnifyText(trabajador_row.telefono) != UnifyText(trabajador_existing.telefono) || UnifyText(trabajador_row.correo_electronico) != UnifyText(trabajador_existing.correo_electronico) {
				// TODO: Ask for confirmation
				err = UpdateTrabajador(db, trabajador_row, trabajador_existing)
				if err != nil {
					return err
				}
			}
		} else {
			if err != nil {
				return err
			}

			err = InsertTrabajador(db, trabajador_row)
			if err != nil {
				return err
			}
		}

		// If becario exists, verify if different for update
		if c, err := ExistsBecario(db, becario_row.curp); c {
			if err != nil {
				return err
			}

			becario_existing, err = GetBecarioByCurp(db, becario_row.curp)
			if err != nil {
				return err
			}

			if UnifyText(becario_row.curp_trabajador) != UnifyText(becario_existing.curp_trabajador) || UnifyText(becario_row.apellido_paterno) != UnifyText(becario_existing.apellido_paterno) || UnifyText(becario_row.apellido_materno) != UnifyText(becario_existing.apellido_materno) || UnifyText(becario_row.nombres) != UnifyText(becario_existing.nombres) || UnifyText(becario_row.curp) != UnifyText(becario_existing.curp) || UnifyText(becario_row.fecha_de_nacimiento) != UnifyText(becario_existing.fecha_de_nacimiento) || UnifyText(becario_row.sexo) != UnifyText(becario_existing.sexo) {
				// TODO: Ask for confirmation
				err = UpdateBecario(db, becario_row, becario_existing)
				if err != nil {
					return err
				}
			}
		} else {
			if err != nil {
				return err
			}

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

			historial_becario_existing, err = GetHistorial_becarioByCurpAnio(db, historial_becario_row.curp_becario, historial_becario_row.anio)
			if err != nil {
				return err
			}

			if UnifyText(historial_becario_row.curp_becario) != UnifyText(historial_becario_existing.curp_becario) || UnifyText(historial_becario_row.anio) != UnifyText(historial_becario_existing.anio) || UnifyText(historial_becario_row.anterior_obtuvo_beca) != UnifyText(historial_becario_existing.anterior_obtuvo_beca) || UnifyText(historial_becario_row.grado_cursado) != UnifyText(historial_becario_existing.grado_cursado) || historial_becario_row.promedio != historial_becario_existing.promedio {
				// TODO: Ask for confirmation
				err = UpdateHistorial_becario(db, historial_becario_row, historial_becario_existing)
				if err != nil {
					return err
				}
			}
		} else {
			if err != nil {
				return err
			}

			err = InsertHistorial_becario(db, historial_becario_row)
			if err != nil {
				return err
			}
		}
	}

	return nil
}
