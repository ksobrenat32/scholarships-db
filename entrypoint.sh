#!/bin/bash

set -e

# This script sets up the environment for the Django application inside a Docker container.

# RUN AS DEMO by default
DEMO=${DEMO:-True}

# If DEMO mode is enabled, we use SQLite for the database.
if [ "$DEMO" = "True" ]; then
    echo "Running in DEMO mode."

    echo "Setting up the database..."
    python manage.py makemigrations
    python manage.py migrate --noinput

    echo "Loading initial data..."
    python manage.py loaddata initial_data.json

    # Create a superuser for testing
    echo "Creating superuser..."
    export DJANGO_SUPERUSER_USERNAME=admin
    export DJANGO_SUPERUSER_EMAIL=admin@example.com
    export DJANGO_SUPERUSER_PASSWORD=admin
    python manage.py createsuperuser --noinput

    # Create test users
    echo "Generating test users..."
    python manage.py generate_users
else
    echo "Running in production mode."
    # Get database configuration from environment variables
    DB_TYPE=${DATABASE_TYPE:-sqlite}
    if [ "$DB_TYPE" != "postgresql" ] && [ "$DB_TYPE" != "sqlite" ]; then
        echo "Invalid DATABASE_TYPE. Expected 'postgresql' or 'sqlite', but got '$DB_TYPE'."
        exit 1
    fi

    echo "Using database type: $DB_TYPE"
    if [ "$DB_TYPE" = "sqlite" ]; then
        echo "Using SQLite database."
        # Ensure the SQLite database file exists
        if [ ! -f /code/db.sqlite3 ]; then
            touch /code/db.sqlite3
        fi
    else
        echo "Using PostgreSQL database."
        DB_HOST=${DB_HOST:-127.0.0.1}
        DB_PORT=${DB_PORT:-5432}
        DB_USER=${DB_USER:-scholarships_user}
        DB_PASSWORD=${DB_PASSWORD:-scholarships_password}

        # Wait for PostgreSQL to be ready
        echo "Waiting for PostgreSQL to start at $DB_HOST:$DB_PORT..."
        while ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
            sleep 1
        done

        echo "PostgreSQL is ready."
        sleep 2  # Additional wait time to ensure PostgreSQL is fully ready
    fi

    echo "Applying database migrations..."
    python manage.py makemigrations
    python manage.py migrate --noinput

    echo "Loading initial data..."
    python manage.py loaddata initial_data.json
fi

echo "Collecting static files..."
python manage.py collectstatic --noinput

PORT=${PORT:-8000}
echo "Using port: $PORT"

# Run the application
echo "Starting the application..."
exec python -m gunicorn becas.wsgi:application --bind "0.0.0.0:$PORT"