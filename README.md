# Full-Stack Docker Architecture (PostgreSQL + FastAPI + Nuxt 4 + Banking Client App)

A complete, production-ready containerized architecture featuring **PostgreSQL 16**, **FastAPI (Python 3.11)**, **Nuxt 4 / Vue 3 (pnpm)**, a **Fintech Banking Client App (React + Vite)**, an **Adminer Database Web Manager**, and a **Makefile** for seamless developer workflows.

---

## 🚀 Architecture Overview

```
                          ┌──────────────────────────┐      ┌──────────────────────────┐
                          │   Banking Client App     │      │   Nuxt 4 Frontend App    │
                          │   http://localhost:3001  │      │   http://localhost:3000  │
                          └─────────────┬────────────┘      └─────────────┬────────────┘
                                        │                                 │
                                        └────────────────┬────────────────┘
                                                         │ REST API
                                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ Docker Network: app-network                                                              │
│                                                                                          │
│  ┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐  │
│  │  client_frontend        │  │  frontend               │  │  backend                │  │
│  │  (Banking Client App)   │  │  (Nuxt 4 / Vue 3)       │  │  (FastAPI + Uvicorn)    │  │
│  │  Port 3001              │  │  Port 3000              │  │  Port 8000              │  │
│  └─────────────────────────┘  └─────────────────────────┘  └────────────┬────────────┘  │
│                                                                         │                │
│  ┌─────────────────────────┐                                            │ SQLAlchemy     │
│  │  adminer (DB UI)        │                                            ▼                │
│  │  http://localhost:8080  ├────────────────────────────────────────► ┌──────────────────┐  │
│  │  (Inspect DB)           │                                          │  db (Postgres)   │  │
│  └─────────────────────────┘                                          │  Port 5433 (Host)│  │
│                                                                       └──────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

### Services Summary

- **Banking Client App (`client_frontend`)**: Mobile/Web Fintech banking interface on [http://localhost:3001](http://localhost:3001) featuring account balances, lifestyle profile badges, interactive transaction search/filtering, and spending analytics.
- **Frontend App (`frontend`)**: Nuxt 4 / Vue 3 / `@nuxt/ui` / Tailwind CSS application running on [http://localhost:3000](http://localhost:3000).
- **Backend (`backend`)**: FastAPI application on [http://localhost:8000](http://localhost:8000) with interactive Swagger OpenAPI docs ([http://localhost:8000/api/docs](http://localhost:8000/api/docs)), health check (`/api/health`), and database seed script.
- **Database Web Management (`adminer`)**: Adminer web GUI on [http://localhost:8080](http://localhost:8080) for inspecting PostgreSQL tables by hand.
- **Database (`db`)**: PostgreSQL 16 Alpine container on host port `5433` / container port `5432` storing `users` and `transactions`.
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
*Seeds PostgreSQL with 5 sample Belgian users (rich demographic/financial profiles) and 500 lifestyle-matched transactions (100 per user).*

### 3. Access Services
- 🏦 **Banking Client App**: [http://localhost:3001](http://localhost:3001) *(Client Banking Dashboard)*
- 🌐 **Nuxt 4 Frontend**: [http://localhost:3000](http://localhost:3000)
- 🗄️ **Adminer DB Inspection UI**: [http://localhost:8080](http://localhost:8080)
  - *Login*: Server: `db`, Username: `postgres`, Password: `postgres`, Database: `tododb`
- ⚡ **FastAPI OpenAPI Docs**: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- 💚 **Backend Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 📋 Makefile Commands Reference

Run `make` or `make help` to view all available commands:

| Command | Description |
| :--- | :--- |
| `make up` (or `make start`) | Start all services in background (with healthchecks) |
| `make seed` | Populate database with 5 sample users & 500 lifestyle transactions |
| `make build` | Rebuild Docker container images |
| `make down` (or `make stop`) | Stop running services |
| `make restart` | Restart all containers |
| `make status` (or `make ps`) | View health and status of containers |
| `make logs` | Tail logs for all services |
| `make logs-client` | Tail logs for Banking Client App (port 3001) |
| `make logs-backend` | Tail logs for FastAPI backend (port 8000) |
| `make logs-frontend` | Tail logs for Nuxt 4 frontend (port 3000) |
| `make logs-db` | Tail logs for PostgreSQL database |
| `make logs-adminer` | Tail logs for Adminer database web UI (port 8080) |
| `make shell-client` | Open interactive shell inside Banking Client container |
| `make shell-backend` | Open interactive bash shell inside backend container |
| `make shell-frontend` | Open interactive shell inside Nuxt 4 container |
| `make shell-db` | Open interactive `psql` shell inside PostgreSQL container |
| `make clean` | Stop stack and purge persistent volumes and network orphans |
