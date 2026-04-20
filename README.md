# Scholarships Database

A web application designed to manage the scholarship database for the Guanajuato Section 37 of the SNTSA.

## Features

-   **User Management**: Workers can register and log in to the system.
-   **Worker and Scholar Profiles**: Workers can create and manage their profiles, as well as the profiles of their children (scholars).
-   **Scholarship Applications**: Workers can submit three types of scholarship applications:
    -   Academic Achievement
    -   Academic Excellence
    -   Special Cases
-   **Application Tracking**: Workers can track the status of their applications.
-   **Admin Interface**: Administrators can manage users, applications, and other data through the Django admin interface.
-   **File Uploads**: The system handles file uploads for required documents (CURP, birth certificates, etc.).

## Project Structure

The project is a standard Django application with the following structure:

-   `becas/`: The main Django project directory.
    -   `settings.py`: Project settings.
    -   `urls.py`: Project-level URL configuration.
    -   `wsgi.py` and `asgi.py`: Server configuration.
-   `becas_sntsa/`: The main application directory.
    -   `models.py`: Database models.
    -   `views.py`: View functions.
    -   `forms.py`: Forms for data input.
    -   `admin.py`: Admin interface configuration.
    -   `templates/`: HTML templates.
    -   `static/`: Static files (CSS, JavaScript, images).
-   `manage.py`: Django's command-line utility.
-   `Dockerfile`: Docker configuration for the application.
-   `requirements.txt`: Python dependencies.

## Models

The application uses the following main models:

-   **Trabajador**: Represents a worker, linked to a Django `User`.
-   **Becario**: Represents a scholar (a worker's child).
-   **Solicitud**: A base model for scholarship applications. It has three subclasses:
    -   **SolicitudAprovechamiento**: For academic achievement scholarships.
    -   **SolicitudExcelencia**: For academic excellence scholarships.
    -   **SolicitudEspecial**: For special case scholarships.
-   **Seccion, Puesto, Jurisdiccion, LugarAdscripcion, Grado**: Supporting models for worker and scholar data.

## Business Logic

### Registration and Application Process

-   **June**: The application period opens. Workers can register, update their information, and create profiles for their children (scholars).
-   Workers can then submit scholarship applications for their children. The system validates the data and ensures that a scholar does not have multiple pending applications of the same type.

### Results

-   **December**: The results for academic excellence scholarships are received (as PDF files). The status of the corresponding applications is updated to "accepted" or "rejected".
-   **June (following year)**: The results for academic achievement and special case scholarships are received (as PDF files). The status of these applications is also updated.

## Setup and Deployment

### Configuration (.env file)

Before running the application in any mode (Native, Demo, or Production), you should configure your environment variables. This is required for everything from database connection to SMTP setup. 

Create a `.env` file in the root of the project by copying the provided template and filling out your values:

```bash
cp .env.example .env
```

Make sure to adjust the variables inside `.env` to suit your database setup and email sender configuration (such as Gmail).

### Native Execution (Development)

To run the application natively without containers, simply use the provided `dev.sh` script (it will automatically load your `.env` file):

```bash
./dev.sh
```

### Demo Mode (Containers)

To run the application in a disposable demo mode (using SQLite) and still test features like email verification, make sure your `.env` file specifically sets `DEMO=True` and `DATABASE_TYPE=sqlite`.

Then, run the provided Docker image passing the environment file:

```bash
podman run --env-file .env -p 8000:8000 ghcr.io/ksobrenat32/scholarships-db:latest
```

This is useful for testing, development, or evaluating the system without setting up a PostgreSQL database.

### Production Mode

For a production environment, it is recommended to use PostgreSQL as the database. The following instructions describe how to set up the application and database using Podman.

#### Pod Configuration

Create a pod to run the application and database containers together:

```bash
podman pod create --name scholarships -p 8000:8000
```

#### Database Container

Start a PostgreSQL container within the pod (it will read database configuration from your `.env` file):

```bash
podman run -d --name scholarships-db \
    --pod scholarships \
    --env-file .env \
    -v /path/to/your/db:/var/lib/postgresql/data:z \
    docker.io/library/postgres:latest
```

#### Application Container

Start the application container, linking it to the database. All configuration is loaded from the `.env` file:

```bash
podman run -d --name scholarships-app \
    --pod scholarships \
    --env-file .env \
    -v /path/to/your/media:/code/media:z \
    ghcr.io/ksobrenat32/scholarships-db:latest
```

#### Create an Admin User

To access the Django admin interface, create a superuser:

```bash
podman exec -it scholarships-app python manage.py createsuperuser
```

### Quadlet Files for Systemd

For easier management, you can use quadlet files to define the containers as systemd services. Create the following files in `~/.config/containers/systemd/`:

**`scholarships.pod`**
```systemd
[Pod]
PodName=scholarships
PublishPort=8000:8000

[Install]
WantedBy=default.target
```

**`scholarships-db.container`**
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

**`scholarships-app.container`**
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

After creating these files, you can start the pod and containers with:

```bash
systemctl --user start scholarships-pod.service
```
