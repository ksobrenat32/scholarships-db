#!/bin/bash

set -e

# This script sets up the environment for the Django application inside a Docker container.

# Source the environment variables
port=$(yq -r '.PORT' /code/config.yaml)
db_host=$(yq -r '.DB_HOST' /code/config.yaml)
db_port=$(yq -r '.DB_PORT' /code/config.yaml)
db_user=$(yq -r '.DB_USER' /code/config.yaml)

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to start..."
while ! pg_isready -h "$db_host" -p "$db_port" -U "$db_user"; do
    sleep 1
done

# Configure the Django settings for production
echo "Applying database migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run the application
echo "Starting the application..."
exec python -m gunicorn becas.wsgi:application --bind "0.0.0.0:$port"