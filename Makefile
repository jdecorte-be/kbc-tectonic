.PHONY: backend frontend help build up down restart logs logs-backend logs-frontend logs-db logs-adminer status ps clean shell-backend shell-frontend shell-db seed setup

# Default target
.DEFAULT_GOAL := help

help: ## Show available commands
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

setup: ## Copy environment variables template if .env does not exist
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ".env file created from .env.example"; \
	else \
		echo ".env file already exists"; \
	fi

build: setup ## Build or rebuild all services
	docker compose build

up: setup ## Start all services in detached mode
	docker compose up -d

start: up ## Alias for 'up'

down: ## Stop all services
	docker compose down

stop: down ## Alias for 'down'

restart: ## Restart all services
	docker compose restart

logs: ## Tail logs for all services
	docker compose logs -f

logs-backend: ## Tail logs for backend service
	docker compose logs -f backend

logs-frontend: ## Tail logs for frontend service
	docker compose logs -f frontend

logs-db: ## Tail logs for database service
	docker compose logs -f db

logs-adminer: ## Tail logs for adminer service
	docker compose logs -f adminer

seed: ## Seed database with sample users and transactions
	docker compose exec -T backend python -m app.seed --force

status: ## Show status of running services
	docker compose ps

ps: status ## Alias for 'status'

clean: ## Stop services and remove volumes, networks, and orphan containers
	docker compose down -v --remove-orphans

shell-backend: ## Open bash shell inside backend container
	docker compose exec backend bash

shell-frontend: ## Open sh shell inside frontend container
	docker compose exec frontend sh

shell-db: ## Open psql interactive shell inside PostgreSQL container
	docker compose exec db psql -U postgres -d tododb

backend: ## Run the backend locally with hot reload (http://localhost:8000)
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend: ## Run the frontend dev server locally
	cd frontend && pnpm dev
