up:
	docker compose up --build

migrate:
	docker compose run --rm api alembic upgrade head

seed:
	docker compose run --rm api python -m app.scripts.seed

test:
	DATABASE_URL=sqlite:///./test.db pytest

docker-test:
	docker compose run --rm api pytest
