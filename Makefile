.PHONY: help prod-build prod-up prod-down prod-logs build up down restart logs logs-backend logs-frontend logs-client logs-db logs-adminer status ps clean shell-backend shell-frontend shell-client shell-db seed setup

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

PROD_COMPOSE := docker compose -f docker-compose.yml -f docker-compose.prod.yml

prod-build: setup ## Build production images
	$(PROD_COMPOSE) build

prod-up: setup ## Build and start the production stack
	$(PROD_COMPOSE) up -d --build

prod-down: ## Stop the production stack
	$(PROD_COMPOSE) down

prod-logs: ## Tail production logs
	$(PROD_COMPOSE) logs -f

down: ## Stop all services
	docker compose down

stop: down ## Alias for 'down'

restart: ## Restart all services
	docker compose restart

logs: ## Tail logs for all services
	docker compose logs -f

logs-backend: ## Tail logs for backend service
	docker compose logs -f backend

logs-frontend: ## Tail logs for Nuxt 4 frontend service
	docker compose logs -f frontend

logs-client: ## Tail logs for Banking Client App service
	docker compose logs -f client_frontend

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

shell-client: ## Open sh shell inside Banking Client container
	docker compose exec client_frontend sh

shell-db: ## Open psql interactive shell inside PostgreSQL container
	docker compose exec db psql -U postgres -d tododb
