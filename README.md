# Scholarships Database

Un programa diseñado para unificar la base de datos usada para la secretaría de becas de Guanajuato Sección 37.

## Reglas de negocio

### Registro

Entran solicitudes en Junio. Se llenan formularios de solicitud de cada unidad con los datos de los becarios y trabajadores.

Se registran nuevos trabajadores y becarios. Se actualizan los datos de los usuarios ya existentes con los nuevos datos, nos basamos en el curp. Se generan solicitudes de becas correspondientes.

### Resultados

En diciembre se reciben archivos pdf con el resultado de becas de excelencia. Se actualizan las solicitudes de becas con aceptación o rechazo.

En junio se reciben archivos pdf con el resultado de becas de aprovechamiento y especiales. Se actualizan las solicitudes de becas con aceptación o rechazo.

## Software

### Sistema

Se divide en módulos para facilitar el desarrollo.

- Interfaz
- [Base de datos](https://github.com/mattn/go-sqlite3)
- [Interacción con hojas de cálculo excel](https://github.com/qax-os/excelize)

### Flujo

1. Usuarios ya existen

P1 "trabajador": CURP - NOMINA_ARCHIVO - INE_ARCHIVO
P2 "becario": CURP BECARIO - BOLETA_ARCHIVO/CERTIFICADOS_ARCHIVO
P3 "registro nuevo" 

2. Nuevo trabajador

PNT "Nuevo trabajador"
- Datos del trabajador

3. Nuevo becario

PNB "Nuevo becario"
- Datos del becario / Si ya es trabajador, solo datos nuevos

4. Registro ya existe

- ¿Actualizar registro? Si/No

### Excel

- Entrada de becas aceptadas
- Salida de todos los registros por año y tipo
- Salida de registros con becas aceptadas por año y tipo
