all: clear configure run

clear:
	rm -rf db/db.sqlite3 becas_sntsa/migrations/0* media/*

configure:
	python3 manage.py makemigrations
	python3 manage.py migrate
	python3 manage.py createsuperuser

run:
	python3 manage.py runserver
