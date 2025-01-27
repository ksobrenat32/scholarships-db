# Scholarships Database

Un programa diseñado para unificar la base de datos usada para la secretaría de becas de Guanajuato Sección 37.

## Como ejecutar

1. Instalar docker o podman
2. Levantar el contenedor

```bash
docker run -d \
    --name scholarships-db \
    -p 8000:8000 \
    -v $(pwd)/db:/code/db:Z \
    -v $(pwd)/media:/code/media:Z \
    ghcr.io/ksobrenat32/scholarships-db:latest
```

3. Crear la base de datos

```bash
docker exec -it scholarships-db python manage.py migrate
```

4. Crear usuario administrador

```bash
docker exec -it scholarships-db python manage.py createsuperuser
```

5. Acceder a la interfaz de administrador en `http://localhost:8000/admin`

## Reglas de negocio

### Registro

Entran solicitudes en Junio. Se llenan formularios de solicitud de cada unidad con los datos de los becarios y trabajadores.

Se registran nuevos trabajadores y becarios. Se actualizan los datos de los usuarios ya existentes con los nuevos datos, nos basamos en el curp. Se generan solicitudes de becas correspondientes.

### Resultados

En diciembre se reciben archivos pdf con el resultado de becas de excelencia. Se actualizan las solicitudes de becas con aceptación o rechazo.

En junio se reciben archivos pdf con el resultado de becas de aprovechamiento y especiales. Se actualizan las solicitudes de becas con aceptación o rechazo.

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

- Un solo trabajador por usuario. Muchos becarios por usuario.
- Con cada solicitud pido los datos del becario para actualizar
- Cada usuario solo puede registrar a sus becarios

### Excel

- Entrada de becas aceptadas
- Salida de todos los registros por año y tipo
- Salida de registros con becas aceptadas por año y tipo
