# Scholarships Database

Un programa diseñado para unificar la base de datos usada para la secretaría de becas de Guanajuato Sección 37.

## Demo

Para ejecutar el programa en modo demo, se utiliza SQLite como base de datos. Esto es útil para pruebas y desarrollo sin necesidad de configurar una base de datos PostgreSQL.

```bash
podman run -p 8000:8000 ghcr.io/ksobrenat32/scholarships-db:latest
```

## Producción

Para ejecutar el programa en un entorno de producción, se recomienda utilizar PostgreSQL como base de datos. Asegúrate de tener configurada la base de datos y las variables de entorno necesarias.

Se recomienda correr con podman en pod para que la aplicación y la base de datos estén en el mismo pod, lo que facilita la comunicación entre ellos.

### Configuración del Pod

Puedes crear un pod para la aplicación y la base de datos utilizando el siguiente comando:

```bash
podman pod create --name scholarships -p 8000:8000
```

### Contenedores de la Aplicación y Base de Datos

Para la base de datos, puedes utilizar el siguiente comando para iniciar un contenedor de PostgreSQL:

```bash
podman run -d --name scholarships-db \
    --pod scholarships \
    -e POSTGRES_DB=scholarships \
    -e POSTGRES_USER=scholarships_user \
    -e POSTGRES_PASSWORD=scholarships_password \
    -v /path/to/your/db:/var/lib/postgresql/data:z \
    docker.io/library/postgres:latest
```

Luego, puedes iniciar el contenedor de la aplicación:

```bash
podman run -d --name scholarships-app \
    --pod scholarships \
    -e SECRET_KEY=your_secret_key \
    -e DEBUG=False \
    -e DEMO=False \
    -e URL=http://127.0.0.1:8000 \
    -e PORT=8000 \
    -e DATABASE_TYPE=postgresql \
    -e POSTGRES_DB=scholarships \
    -e POSTGRES_USER=scholarships_user \
    -e POSTGRES_PASSWORD=scholarships_password \
    -e POSTGRES_HOST=localhost \
    -e POSTGRES_PORT=5432 \
    -v /path/to/your/media:/code/media:z \
    ghcr.io/ksobrenat32/scholarships-db:latest
```

### Crear usuario administrador

Para crear un usuario administrador que pueda acceder al panel de administración, puedes ejecutar el siguiente comando:

```bash
podman exec -it scholarships-app python manage.py createsuperuser
```

### Acceso a la Aplicación

En caso de que estés utilizando un proxy inverso, asegúrate de que esté configurado correctamente para redirigir las solicitudes al contenedor de la aplicación. El puerto default es `8000`, pero puedes cambiarlo según tus necesidades.

Ejemplo con caddy:

```Caddyfile
mi_dominio.com {
    reverse_proxy localhost:8000
}
```

### Archivos quadlet

Para administrar los contenedores de manera más sencilla, puedes utilizar archivos quadlet. Estos archivos permiten definir la configuración del contenedor de manera declarativa.

En primer lugar debes crear un archivo de configuración. Te puedes guiar del archivo `.env.example` para definir las variables de entorno necesarias.

Los archivos de configuración deben estar en `~/.config/containers/systemd/` y deben tener la extensión `.container` o `.pod`.

`scholarships.pod`:

```systemd
[Pod]
PodName=scholarships
PublishPort=8000:8000

[Install]
WantedBy=default.target
```

`scholarships-db.container`:

```systemd
[Unit]
Description=Scholarships database container

[Container]
ContainerName=scholarships-db
Image=docker.io/library/postgres:latest
EnvironmentFile=/path/to/your/.env
AutoUpdate=registry
Pod=scholarships.pod
Volume=/path/to/your/db:/var/lib/postgresql/data:z

[Install]
WantedBy=default.target
```

`scholarships-app.container`:

```systemd
[Unit]
Description=Scholarships application container
DependsOn=scholarships-db.service

[Container]
ContainerName=scholarships-app
Image=ghcr.io/ksobrenat32/scholarships-db:latest
EnvironmentFile=/path/to/your/.env
AutoUpdate=registry
Pod=scholarships.pod
Volume=/path/to/your/media:/code/media:z

[Install]
WantedBy=default.target
```

Una vez que tengas estos archivos en `~/.config/containers/systemd/`, puedes iniciar el pod y los contenedores con:

```bash
systemctl --user start scholarships-pod.service
```

## Reglas de negocio

### Registro

Entran solicitudes en Junio. Se llenan formularios de solicitud de cada unidad con los datos de los becarios y trabajadores.

Se registran nuevos trabajadores y becarios. Se actualizan los datos de los usuarios ya existentes con los nuevos datos, nos basamos en el curp. Se generan solicitudes de becas correspondientes.

### Resultados

En diciembre se reciben archivos pdf con el resultado de becas de excelencia. Se actualizan las solicitudes de becas con aceptación o rechazo.

En junio se reciben archivos pdf con el resultado de becas de aprovechamiento y especiales. Se actualizan las solicitudes de becas con aceptación o rechazo.
