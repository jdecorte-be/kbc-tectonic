.PHONY: help setup install up build down logs status backend frontend test check
.DEFAULT_GOAL := help
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

test: ## Test the workflow and adapters without paid API calls
	PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v

check: test ## Typecheck and build the frontend
	cd frontend && pnpm typecheck && pnpm build
