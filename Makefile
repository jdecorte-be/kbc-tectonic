.PHONY: help setup install up build down logs status backend frontend seed seed-local test check
.DEFAULT_GOAL := help
COUNT ?= 1000
export PATH := $(CURDIR)/.tools/node/bin:$(CURDIR)/.tools/pnpm/node_modules/.bin:$(PATH)

help: ## KBC + Jev demo commands
	@awk 'BEGIN {FS = ":.*?## "}; /^[a-zA-Z_-]+:.*?## / {printf "  %-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Create .env if absent (exported keys also work)
	@test -f .env || cp .env.example .env

install: ## Install Python and Nuxt dependencies (Python 3.11+, Node 22+, pnpm 12)
	python3 -m venv .venv
	.venv/bin/python -m pip install -r backend/requirements.txt
	cd frontend && pnpm install --frozen-lockfile

up: setup ## Build and start Docker demo on localhost:3000
	docker compose up --build -d

build: ## Build Docker images
	docker compose build

down: ## Stop containers
	docker compose down

logs: ## Follow logs
	docker compose logs -f

status: ## Show container status
	docker compose ps

backend: ## Start FastAPI on localhost:8000
	.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000

frontend: ## Start Nuxt on localhost:3000 (another terminal)
	cd frontend && pnpm dev --host 127.0.0.1 --port 3000

seed: ## Seed synthetic clients; use running Docker backend or local Python (COUNT=1000)
	@if command -v docker >/dev/null 2>&1 && docker compose ps --status running --services 2>/dev/null | grep -qx backend; then \
		docker compose exec -T backend python -m app.seed --count "$(COUNT)"; \
	else \
		PYTHONPATH=backend .venv/bin/python -m app.seed --count "$(COUNT)"; \
	fi

seed-local: ## Seed through local Python and configured DATABASE_URL (COUNT=1000)
	PYTHONPATH=backend .venv/bin/python -m app.seed --count "$(COUNT)"

test: ## Test the workflow and adapters without paid API calls
	PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v

check: test ## Typecheck and build the frontend
	cd frontend && pnpm typecheck && pnpm build
