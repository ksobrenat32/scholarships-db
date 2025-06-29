#!/bin/bash
set -e
# This script sets a test environment using Podman.

# Clean up any existing containers
podman rm -f scholarships-db

# Clean all the media files
rm -rf ./media/*ps-db

# Run the PostgreSQL container with the necessary environment variables
podman run -d --name scholarships-db -e POSTGRES_DB=scholarships -e POSTGRES_USER=scholarships_user -e POSTGRES_PASSWORD=scholarships_password -p 5432:5432 docker.io/postgres:latest

# Wait for the PostgreSQL container to be ready
echo "Waiting for PostgreSQL to start..."
while ! podman exec scholarships-db pg_isready -U scholarships_user; do
    sleep 1
done

# Configure the Django settings for testing
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata initial_data.json

# Create a superuser for testing
export DJANGO_SUPERUSER_USERNAME=admin
export DJANGO_SUPERUSER_EMAIL=admin@example.com
export DJANGO_SUPERUSER_PASSWORD=admin
python manage.py createsuperuser --noinput

# Create test users
python manage.py generate_users

# Start the Django development server
python manage.py runserver

