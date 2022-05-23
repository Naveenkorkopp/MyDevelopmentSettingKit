
bash:
	docker-compose run --user=$(shell id -u) ${service} bash

# Build docker image
build:
	docker-compose build

restart:
	docker-compose restart '${service}'

run:
	docker-compose up -d

up:
	docker-compose up

logs:
	docker-compose logs

# Removes old containers, free's up some space
remove:
	# Try this if this fails: docker rm -f $(docker ps -a -q)
	docker-compose rm --force -v

stop:
	docker-compose stop

clean: stop remove

log:
	docker-compose logs -f '${service}'

superuser:
	docker-compose exec webserver python manage.py createsuperuser
