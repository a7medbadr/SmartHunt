lint:
	cd backend && uv run ruff check .

format-check:
	cd backend && uv run black .

test:
	cd backend && uv run pytest --envfile=../.env

compile:
	cd backend && uv run python -m compileall src

helm-lint:
	helm lint helm/smarthunt

helm-template:
	helm template smarthunt helm/smarthunt >/dev/null

docker-build:
	docker build -t smarthunt-backend:latest backend
