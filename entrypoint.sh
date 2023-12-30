#!/bin/sh

#if [ "$DATABASE" = "attendify" ]; then
#    echo "Waiting for postgres..."
#
#    while ! nc -z $DATABASE_HOST $DATABASE_PORT; do
#      sleep 0.1
#    done
#
#    echo "PostgreSQL started"
#fi

# Make migrations and migrate the database.
echo "Making migrations and migrating the database. "
python manage.py makemigrations --noinput 
python manage.py migrate --noinput 
python manage.py collectstatic --noinput
gunicorn kedarnath.wsgi:application --bind 0.0.0.0:8000 --workers=4

exec "$@"
