# Scholarships Database

Un programa diseñado para unificar la base de datos usada para la secretaría de becas de Guanajuato Sección 37.

## Como ejecutar

1. Levantar el contenedor de la base de datos

   ```bash
   podman run -d --name scholarships-db \
       -e POSTGRES_DB=scholarships \
       -e POSTGRES_USER=scholarships_user \
       -e POSTGRES_PASSWORD=scholarships_password \
       -p 5432:5432 \
       podman.io/postgres:latest
   ```

2. Levantar el contenedor de la aplicación

    ```bash
    podman run -d \
        --name scholarships \
        -p 8000:8000 \
        -v $(pwd)/config.yaml:/code/config.yaml:Z,ro \
        -v $(pwd)/media:/code/media:Z \
        ghcr.io/ksobrenat32/scholarships-db:latest
    ```

## Configuración

El archivo de configuración `config.yaml` debe ser configurado con los parámetros necesarios para la aplicación. Dentro de este archivo, se pueden definir los mismos.

1. Inicialización de la base de datos

    ```bash
    podman exec -it scholarships-db python manage.py migrate
    podman exec -it scholarships-db python manage.py loaddata initial_data.json
    ```

2. Crear un superusuario para acceder al panel de administración

    ```bash
    podman exec -it scholarships-db python manage.py createsuperuser
    ```

3. Crear información de prueba

    ```bash
    podman exec -it scholarships-db python manage.py generate_users
    ```

## Reglas de negocio

### Registro

Entran solicitudes en Junio. Se llenan formularios de solicitud de cada unidad con los datos de los becarios y trabajadores.

Se registran nuevos trabajadores y becarios. Se actualizan los datos de los usuarios ya existentes con los nuevos datos, nos basamos en el curp. Se generan solicitudes de becas correspondientes.

### Resultados

En diciembre se reciben archivos pdf con el resultado de becas de excelencia. Se actualizan las solicitudes de becas con aceptación o rechazo.

En junio se reciben archivos pdf con el resultado de becas de aprovechamiento y especiales. Se actualizan las solicitudes de becas con aceptación o rechazo.
