ENV_FILE = --env-file .env.development
COMPOSE  = docker compose -f docker-compose.dev.yml $(ENV_FILE)

up:
	$(COMPOSE) up -d

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
