# KBC Tectonic

Hackathon project for KBC. It reads a client's bank transactions, works out their **habits**, and from those infers **life-stage profiles** (student, investor, going on holiday, new parent, …). Each profile has a confidence score, the reasons behind it, and a suggested next best offer.

> All data is synthetic. Never commit real client data.

## What it does

- **Habit engine** groups transactions by category (income, housing, mobility, investing, travel, …) and measures spending rhythm, recurring payments, savings rate and month-over-month drift.
- **Profiling engine** turns habits into one or more profiles per client. It is rule-based and explainable: every profile lists the signals that triggered it.
- **Jev AI (optional)** asks the TypeSafe System One API for a second, probabilistic profile per client.
- **Advisor dashboard** (Nuxt) shows the client list, profile badges, segment distribution, habit trends, alerts, and a graph of related clients.
- **Client app** (React) is a mock banking app showing the client's own view: balance, profile badges, transactions and spending analytics.

### Profiles

| Core | Extra |
| :--- | :--- |
| Student · Young investor · Investor · Holiday soon | New parent / family · Homebuyer / mover · Car owner / commuter · Freelancer · Saver · Financial stress · Retiree · Big event |

The profile catalogue, with offers and "looks for" signals, is defined in `backend/app/profiles.py`.

## Architecture

```
 Advisor dashboard (Nuxt 4)   :3000 ─┐
 Client app (React + Vite)    :3001 ─┼─ REST ──► Backend (FastAPI) :8000 ──► PostgreSQL 16 :5433
                                     │                 │
 Adminer (DB UI)              :8080 ─┘                 └──► Jev AI API (optional)
```

| Path | Stack | Role |
| :--- | :--- | :--- |
| `backend/` | FastAPI, SQLAlchemy, Pydantic | API, seed data, habit and profiling engines, Jev client |
| `frontend/` | Nuxt 4, Nuxt UI, shadcn-vue, Tailwind v4, Unovis | Advisor dashboard |
| `client-app/` | React 18, Vite, TypeScript | Client-facing banking app |

## Quick start

You need Docker (with Compose v2) and `make`.

```bash
make up      # creates .env from .env.example if missing, then starts all services
make seed    # (re)seeds ~105 synthetic Belgian clients with a year of transactions each
```

| Service | URL |
| :--- | :--- |
| Advisor dashboard | http://localhost:3000 |
| Client app | http://localhost:3001 |
| API docs (Swagger) | http://localhost:8000/api/docs |
| Adminer | http://localhost:8080 (server `db`, user/password `postgres`, database `tododb`) |

To enable Jev AI profiling, set `JEV_API_KEY` in `.env` and run `make restart`. Without the key, the `/api/jev/*` endpoints return `503`. Everything else still works.

## API

The full reference is at `/api/docs` or in [`OPENAPI.md`](OPENAPI.md). Main endpoints:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/dashboard` | KPIs, segment distribution, habit trends, weekday rhythm |
| `GET` | `/api/clients`, `/api/clients/{id}` | Profiled clients with habits, profiles, reasons and offers |
| `GET` | `/api/profiles` | Profile catalogue |
| `GET` | `/api/relations` | Related clients (household links and similar profiles) |
| `GET/POST` | `/api/users`, `/api/transactions` | Raw users and transactions |
| `POST` | `/api/seed` | Seed the database |
| `GET/POST` | `/api/jev/clients` | Read cached Jev results, or run Jev over all clients |
| `GET` | `/api/health` | API and database health |

Clients are profiled live from the `users` and `transactions` tables on every request. Nothing is precomputed.

## Development

**Frontend** (run in `frontend/`, use pnpm):

```bash
pnpm install
pnpm dev
pnpm lint && pnpm typecheck
pnpm gen:api   # regenerate app/types/api.gen.ts from the running backend's OpenAPI spec
```

To get typed API data, add a Pydantic `response_model` in `backend/app/schemas.py`, run `pnpm gen:api`, and import the types from `@/types/api`.

**Backend**: in Docker, the `backend/` folder is mounted into the container and Uvicorn hot-reloads on changes. Use `make shell-backend` to open a shell there.

## Make commands

Run `make help` to see all targets.

| Command | Description |
| :--- | :--- |
| `make up` / `make down` | Start / stop the dev stack |
| `make build` / `make restart` | Rebuild images / restart containers |
| `make seed` | Drop and reseed the database |
| `make logs`, `make logs-<service>` | Tail logs (`backend`, `frontend`, `client`, `db`, `adminer`) |
| `make shell-<service>` | Open a shell (`backend`, `frontend`, `client`, `db`) |
| `make status` | Show container status |
| `make clean` | Stop and delete all volumes (wipes the database) |
| `make prod-up` / `make prod-down` | Build and run the production stack (no bind mounts; Adminer disabled) |
