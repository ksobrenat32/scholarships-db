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
docker exec -it scholarships-db python manage.py loaddata initial_data.json
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
