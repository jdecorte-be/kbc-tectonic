# Full-Stack Docker Architecture (PostgreSQL + FastAPI + Nuxt 4)

A complete, production-ready containerized architecture featuring **PostgreSQL 16**, **FastAPI (Python 3.11)**, **Nuxt 4 / Vue 3 (pnpm)**, an **Adminer Database Web Manager**, and a **Makefile** for seamless developer workflows.

---

## 🚀 Architecture Overview

```
                                  ┌──────────────────────────┐
                                  │   Browser / Client UI    │
                                  │   http://localhost:3000  │
                                  └─────────────┬────────────┘
                                                │
                                                │ API / Custom
                                                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Docker Network: app-network                                               │
│                                                                          │
│  ┌───────────────────────┐                  ┌─────────────────────────┐  │
│  │   frontend            │                  │   backend               │  │
│  │   (Node 20 + Nuxt 4)  │                  │   (FastAPI + Uvicorn)   │  │
│  │   Port 3000           │                  │   Port 8000             │  │
│  └───────────────────────┘                  └────────────┬────────────┘  │
│                                                          │               │
│  ┌───────────────────────┐                               │ SQLAlchemy    │
│  │   adminer (DB UI)     │                               ▼               │
│  │   http://localhost:8080├───────────────────► ┌─────────────────────────┐  │
│  │   (Inspect DB)        │                    │   db                    │  │
│  └───────────────────────┘                    │   (PostgreSQL 16)       │  │
│                                               │   Port 5433 (Host)      │  │
│                                               └─────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

### Components

- **Database (`db`)**: PostgreSQL 16 Alpine with `pg_isready` health checks and persistent volume (`postgres_data`).
- **Database Web Management (`adminer`)**: Adminer web GUI on [http://localhost:8080](http://localhost:8080) for inspecting and querying PostgreSQL by hand.
- **Backend (`backend`)**: FastAPI application with SQLAlchemy ORM, Pydantic validation, health status check, interactive Swagger docs ([http://localhost:8000/api/docs](http://localhost:8000/api/docs)), live reloading, and database seed script (`app.seed`).
- **Frontend (`frontend`)**: Nuxt 4 / Vue 3 / `@nuxt/ui` / Tailwind CSS / pnpm application running on port `3000`.
- **Makefile**: Unified command interface for setup, startup, database seeding, status inspection, logging, and shell access.

---

## 🛠️ Quick Start Guide

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose v2+](https://docs.docker.com/compose/)
- `make` (GNU Make)

### 1. Start the Stack
```bash
make up
```

### 2. Seed the Database
```bash
make seed
```
*Seeds PostgreSQL with sample Users (names, phone numbers, emails, addresses) and Transactions (deposits, payments, withdrawals, transfers).*

### 3. Access Services
- **Nuxt 4 Frontend**: [http://localhost:3000](http://localhost:3000)
- **Adminer DB Inspection UI**: [http://localhost:8080](http://localhost:8080)
  - *Login*: Server: `db`, Username: `postgres`, Password: `postgres`, Database: `tododb`
- **FastAPI OpenAPI Docs**: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- **Backend Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 📋 Makefile Commands Reference

Run `make` or `make help` to view all available commands:

| Command | Description |
| :--- | :--- |
| `make up` (or `make start`) | Start all services in background (with healthchecks) |
| `make seed` | Populate database with sample Users and Transactions |
| `make build` | Rebuild Docker container images |
| `make down` (or `make stop`) | Stop running services |
| `make restart` | Restart all containers |
| `make status` (or `make ps`) | View health and status of containers |
| `make logs` | Tail logs for all services |
| `make logs-backend` | Tail logs for FastAPI backend |
| `make logs-frontend` | Tail logs for Nuxt 4 frontend |
| `make logs-db` | Tail logs for PostgreSQL database |
| `make logs-adminer` | Tail logs for Adminer database web UI |
| `make shell-backend` | Open an interactive bash shell in backend container |
| `make shell-frontend` | Open an interactive shell in frontend container |
| `make shell-db` | Open interactive `psql` shell in database container |
| `make clean` | Stop stack and purge persistent volumes and network orphans |

---

## 📡 REST API Endpoints

### Database & Health
- `GET /api/health` - Check API and PostgreSQL database status
- `POST /api/seed` - Trigger database seeding (`?force=true` to reset)

### Users (`/api/users`)
- `GET /api/users` - List all users
- `GET /api/users/{user_id}` - Get user details with transaction history
- `POST /api/users` - Create a new user (`name`, `phone_number`, `email`, `address`, `city`, `country`)

### Transactions (`/api/transactions`)
- `GET /api/transactions` - List all transactions (optional `?user_id=1` filter)
- `POST /api/transactions` - Create a transaction (`user_id`, `amount`, `currency`, `transaction_type`, `status`, `description`)
