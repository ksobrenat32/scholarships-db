#!/bin/bash

set -e

# This script sets up the environment for the Django application inside a Docker container.

# Source the environment variables
db_host=$(yq eval '.db_host' /code/config.yaml)
db_port=$(yq eval '.db_port' /code/config.yaml)
db_user=$(yq eval '.db_user' /code/config.yaml)

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to start..."
while ! pg_isready -h "$db_host" -p "$db_port" -U "$db_user"; do
    sleep 1
done

# Configure the Django settings for production
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Run the application
exec gunicorn becas.wsgi:application --bind