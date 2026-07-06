ENV_FILE = --env-file .env.development
COMPOSE  = docker compose -f docker-compose.dev.yml $(ENV_FILE)

up:
	$(COMPOSE) up -d

build:
	$(COMPOSE) build

rebuild:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart

logs:
	$(COMPOSE) logs -f

migrate:
	$(COMPOSE) exec web python3 manage.py migrate

makemigrations:
	$(COMPOSE) exec web python3 manage.py makemigrations

createsuperuser:
	$(COMPOSE) exec web python3 manage.py createsuperuser

shell:
	$(COMPOSE) exec web python3 manage.py shell

collectstatic:
	$(COMPOSE) exec web python3 manage.py collectstatic --noinput

loaddata:
	$(COMPOSE) exec web python3 manage.py loaddata prefectures
	$(COMPOSE) exec web python3 manage.py loaddata activity_types
	$(COMPOSE) exec web python3 manage.py loaddata ski_resorts

setup:
	$(COMPOSE) up -d
	$(COMPOSE) exec web python3 manage.py migrate
	$(COMPOSE) exec web python3 manage.py loaddata prefectures
	$(COMPOSE) exec web python3 manage.py loaddata activity_types
	$(COMPOSE) exec web python3 manage.py loaddata ski_resorts

test:
	$(COMPOSE) exec web python3 manage.py test

test-app:
	$(COMPOSE) exec web python3 manage.py test accounts_app

app-login:
	$(COMPOSE) exec web bash

db-login:
	$(COMPOSE) exec db bash
	
dbshell:
	$(COMPOSE) exec db bash -c 'psql -U $$POSTGRES_USER -d $$POSTGRES_DB'