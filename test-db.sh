#!/bin/bash

# This script sets up a PostgreSQL database for the scholarships application using Podman. Useful for local development and testing. The database is deleted with the container, so it is not persistent.

podman run -d --name scholarships-db -e POSTGRES_DB=scholarships -e POSTGRES_USER=scholarships_user -e POSTGRES_PASSWORD=scholarships_password -p 5432:5432 docker.io/postgres:latest

