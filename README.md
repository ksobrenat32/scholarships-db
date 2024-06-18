# Scholarships Database

Un programa diseñado para unificar la base de datos usada para la secretaría de becas de Guanajuato Sección 37.

## Descripción

El programa recibe como entrada las hojas de cálculo en formato excel de cada unidad y a partir de estas genera una base de datos con los datos de los trabajadores y del becario.

Con estas posteriormente se puede introducir CURP con la cual se realiza el llenado del resto de datos. En caso de no estar registrado se genera el nuevo registro y en caso de ya estarlo se pregunta si se desean actualizar datos mostrando la comparación entre versiones.

### Sistema

El programa esta escrito en GO de tal forma que pueda ser ejecutado en distintos sistemas operativos (GNU/Linux y Windows) mediante un solo ejecutable estático. Se ejecutara solo de forma local y en ambientes de confianza. No olvidando el trato que deben tener los datos privados de los trabajadores.

Se divide en módulos para facilitar el desarrollo.

- Interfaz
- [Base de datos](https://github.com/mattn/go-sqlite3)
- [Interacción con hojas de cálculo excel](https://github.com/qax-os/excelize)

### Flujo

### Generación de la base de datos

1. Entra el archivo de excel de cada unidad
2. Se almacenan los promedios de los becarios que se encuentren registrados.
3. Se registran los trabajadores y becarios nuevos
4. Se notifica en caso de existir diferencia de los trabajadores o becarios nuevos

### Generación de hoja de datos

1. Entra excel con nombre completo de trabajadores
2. Se pregunta sobre los trabajadores no registrados
2. Se pregunta en caso de existir distintos trabajadores con el mismo nombre
3. Se pregunta en caso de que el trabajador cuente con mas de un becario registrado
4. Se devuelve una hoja de excel y archivo sqlite3 con todos los datos obtenidos de los trabajadores registrados

## Diseño base de datos

La base de datos almacena todos los datos de los trabajadores, cuenta con la misma estructura que la hoja de cálculo en formato excel con la que se registran las unidades, incluyendo una relación con el historial de calificaciones de cada becario

Trabajadores:

- id (INTEGER PRIMARY KEY)
- seccion (VARCHAR(256) NOT NULL)
- apellido_paterno (VARCHAR(256) NOT NULL)
- apellido_materno (VARCHAR(256))
- nombre (VARCHAR(256) NOT NULL)
- curp (VARCHAR(256) NOT NULL)
- codigo_de_puesto (VARCHAR(256) NOT NULL)
- lugar_de_adscripcion (VARCHAR(256) NOT NULL)
- telefono (VARCHAR(256) NOT NULL)
- correo_electronico (VARCHAR(256) NOT NULL)

Becarios:

- id (INTEGER PRIMARY KEY)
- curp_trabajador (VARCHAR(256) NOT NULL)
- apellido_paterno (VARCHAR(256) NOT NULL)
- apellido_materno (VARCHAR(256) NOT NULL)
- nombre (VARCHAR(256) NOT NULL)
- curp (VARCHAR(256) NOT NULL)
- fecha_de_nacimiento (VARCHAR(256) NOT NULL)
- sexo (VARCHAR(256) NOT NULL)

Datos de becario:

- id (INTEGER PRIMARY KEY)
- curp_becario (VARCHAR(256) NOT NULL)
- anio (VARCHAR(256) NOT NULL)
- anterior_obtuvo_beca (VARCHAR(256) NOT NULL)
- grado_cursado (VARCHAR(256) NOT NULL)
- promedio (FLOAT NOT NULL)
