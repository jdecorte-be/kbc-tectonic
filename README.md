# Docker Full-Stack Architecture (PostgreSQL + FastAPI + React Vite)

A complete, production-ready containerized full-stack Todo application built with **PostgreSQL 16**, **FastAPI (Python 3.11)**, and **React 18 + Vite (TypeScript)**, fully orchestrated with **Docker Compose** and managed via a comprehensive **Makefile**.

---

## 🚀 Architecture Overview

```
                          ┌──────────────────────────┐
                          │   Browser / Client UI    │
                          │   http://localhost:5173  │
                          └─────────────┬────────────┘
                                        │
                                        │ Proxy /api
                                        ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Docker Network: app-network                                               │
│                                                                          │
│  ┌───────────────────────┐                  ┌─────────────────────────┐  │
│  │   frontend            │                  │   backend               │  │
│  │   (Node 20 + Vite)    │                  │   (FastAPI + Uvicorn)   │  │
│  │   Port 5173           │                  │   Port 8000             │  │
│  └───────────────────────┘                  └────────────┬────────────┘  │
│                                                          │               │
│                                                          │ SQLAlchemy    │
│                                                          ▼               │
│                                             ┌─────────────────────────┐  │
│                                             │   db                    │  │
│                                             │   (PostgreSQL 16)       │  │
│                                             │   Port 5432             │  │
│                                             └─────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

### Components

- **Database (`db`)**: PostgreSQL 16 Alpine with custom health checks and persistent volume storage (`postgres_data`).
- **Backend (`backend`)**: FastAPI application with SQLAlchemy ORM, Pydantic schemas, auto-migrations on start, health status check, interactive Swagger docs (`http://localhost:8000/api/docs`), and live code reloading in container.
- **Frontend (`frontend`)**: React 18 + Vite + TypeScript application with hot module replacement (HMR), real-time system status indicators, and full CRUD Todo interface.
- **Makefile**: Unified command interface for single-command setup, execution, logging, status monitoring, and shell access.

---

## 🛠️ Quick Start Guide

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose v2+](https://docs.docker.com/compose/)
- `make` (GNU Make)

### 1. Start the entire application stack
```bash
make up
```
*This command automatically sets up `.env` from `.env.example` if needed, builds container images, and starts all services in the background.*

### 2. View Service Status
```bash
make status
```

### 3. Open in Browser
- **Frontend Application**: [http://localhost:5173](http://localhost:5173)
- **FastAPI OpenAPI Swagger Documentation**: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
- **Backend Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 📋 Makefile Commands Reference

Run `make` or `make help` to view all available commands:

| Command | Description |
| :--- | :--- |
| `make up` (or `make start`) | Start all services in background (with healthchecks) |
| `make build` | Rebuild Docker container images |
| `make down` (or `make stop`) | Stop running services |
| `make restart` | Restart all containers |
| `make status` (or `make ps`) | View health and status of containers |
| `make logs` | Tail logs for all services |
| `make logs-backend` | Tail logs for FastAPI backend |
| `make logs-frontend` | Tail logs for React/Vite frontend |
| `make logs-db` | Tail logs for PostgreSQL database |
| `make shell-backend` | Open an interactive bash shell in the backend container |
| `make shell-frontend` | Open an interactive shell in the frontend container |
| `make shell-db` | Open interactive `psql` shell in the database container |
| `make clean` | Stop stack and purge persistent volumes and network orphans |

---

## ⚙️ Environment Variables (`.env`)

```env
# PostgreSQL Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=tododb
POSTGRES_PORT=5432
POSTGRES_HOST=db

# Backend Configuration
DATABASE_URL=postgresql://postgres:postgres@db:5432/tododb
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173

# Frontend Configuration
VITE_API_BASE_URL=http://localhost:8000
```

---

## 📡 REST API Endpoints

### Health & Connectivity
- `GET /api/health` - Check API and PostgreSQL database health

### Todo Resource (`/api/todos`)
- `GET /api/todos` - List all todos (optional `?completed=true|false` filter)
- `POST /api/todos` - Create a new todo (`{"title": "Task", "description": "Details"}`)
- `GET /api/todos/{id}` - Fetch a specific todo by ID
- `PUT /api/todos/{id}` - Update todo title, description, or completion status
- `DELETE /api/todos/{id}` - Delete todo task

---

## 🧹 Teardown

To stop and completely remove container volumes (resetting database state):
```bash
make clean
```
