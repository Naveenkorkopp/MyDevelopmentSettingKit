#!/bin/bash
set -e
cmd="$@"


if [ "$DJANGO_DB_HOST" ] && [ "$DJANGO_DB_USER" ] && [ "$DJANGO_DB_PASSWORD" ]; then
  export DATABASE_URL=postgres://$DJANGO_DB_USER:$DJANGO_DB_PASSWORD@$DJANGO_DB_HOST:$DJANGO_DB_PORT/$DJANGO_DB_NAME
else
  export DATABASE_URL=postgres://postgres:postgres@postgres:5432/seiu_db
fi

function postgres_ready(){
python << END
import sys
import psycopg2
try:
    conn = psycopg2.connect("$DATABASE_URL")
except psycopg2.OperationalError:
    sys.exit(-1)
sys.exit(0)
END
}

until postgres_ready; do
 >&2 echo "Postgres is unavailable - sleeping"
 sleep 1
done
>&2 echo "Postgres is up - continuing..."


# -z tests for empty, if TRUE, $cmd is empty, run migrate only when using postgres DB locally
if [ -z $cmd ]; then
  >&2 echo "Running collectstatic command..."
    python manage.py collectstatic --clear --noinput
  >&2 echo "Running migrate command..."
    python manage.py migrate --noinput
  # start server
  >&2 echo "Running SEIU Backend Server...(gunicorn)"
    gunicorn config.wsgi -w 4 -b 0.0.0.0:8000 -t 12000 -k gevent --chdir=/app
else
  >&2 echo "Running command passed (by the compose file)"
  exec $cmd
fi
