# KBC Tectonic

A hackathon demo that uses synthetic banking data, TypeSafe Jev and OpenAI to understand customer profiles and suggest relevant product adverts. When evidence is insufficient, the workflow returns **UNKNOWN** or no advert.

## Quick start with Docker

Requirements: Docker with Docker Compose.

```sh
make setup
```

Edit the root `.env` and fill in `JEV_API` and `OPENAI_API_KEY`. `make setup` preserves any existing `.env`; API keys are used only by the backend.

```sh
make up
```

- App: **http://localhost:3000**
- API docs: **http://localhost:8000/api/docs**
- Database browser: **http://localhost:8080** (Adminer)
- Logs: `make logs`
- Stop: `make down`

## Local development

Requirements: Python 3.11+, Node.js 22+ and pnpm 12.6.0.

Configure `.env` as above, then install dependencies:

```sh
make install
```

Start the backend in one terminal:

```sh
make backend
```

Start the frontend in another terminal at the repository root:

```sh
make frontend
```

The app and API URLs are the same. Nuxt forwards API requests to `http://127.0.0.1:8000` by default; override this with `NUXT_API_BASE`.

## Browse the database

`make up` includes Adminer. To start only PostgreSQL and Adminer:

```sh
make adminer
make seed     # Populate an empty Docker database with synthetic customers
```

Open **http://localhost:8080** and log in with:

| Field | Value |
| --- | --- |
| System | PostgreSQL |
| Server | `db` |
| Username | `postgres` |
| Password | `postgres` |
| Database | `kbc` |

Adminer views the Docker PostgreSQL database. Local development uses a separate SQLite database by default; its customers and saved runs will not appear in Adminer.

## How it works

- The dashboard summarizes observed profiles, cash flow and the latest selected adverts, with interactive customer connections and an **Opt-in only** filter. Filters apply to the full population; the graph shows a labelled sample.
- Client context explains habits such as **Young investor**, **Saver** and **Student activity** from observed transactions. Saved AI decisions and unanalysed clients are shown separately.
- Select a customer, run the workflow and inspect their transactions, inferred profile, supporting evidence and adverts.
- Each Jev category question includes `UNKNOWN`. On `UNKNOWN`, OpenAI may identify a supported category; the registry saves its definition, question and customer assignment for future Jev runs.
- Insufficient evidence remains `UNKNOWN`. Customers who opted out of personalization receive no adverts.
- Benchmark **10, 100 or 1,000 customers** to compare results, elapsed time, throughput and estimated API cost in USD. These are real workflow runs; estimates exclude hosting costs.

## Generate synthetic users

```sh
make seed                 # 1,000 generated clients + one limited-history example
make seed COUNT=100        # Choose the population size for a fresh database
make seed-local COUNT=100  # Force local Python instead of the running Docker backend
```

`make seed` uses the running Docker backend first. If only Docker PostgreSQL is running, it builds a temporary backend container to seed it. Otherwise it uses `.venv/bin/python`; `make seed-local` always uses the local database configuration (SQLite by default). It generates transactions and imports the product catalogue without AI calls. Repeating it reuses existing records. To change the population size, configure a fresh `DATABASE_URL`; the command never replaces existing customer evidence. Run it before the first backend startup to choose a custom size.

## Data and persistence

- If the database is empty, first startup imports **1,001 synthetic customers** from `generate_bank_profiles.py` and the catalogue from `products.json`. Following startups reuse the database.
- Customers, accounts, transactions and products use SQLAlchemy: **PostgreSQL 16 in Docker**, **SQLite locally**. Imports are validated and atomic; monetary values are stored in integer cents.
- Analyses, benchmark results, timings and costs are persisted. Open **Analysis history** or **Benchmark history** in the app to view them without new AI calls.
- Interrupted benchmarks retain completed results and are marked failed after restart. Run one API process; jobs use bounded asynchronous concurrency within it.
- Learned categories, questions and assignments remain in the SQLite registry. Docker volumes preserve both databases across `make down`.

Optional database URLs, source files, models and cost rates are in `.env.example`. For a separate dataset, use fresh `DATABASE_URL` and `CATEGORY_DB_PATH` locations. API docs include paginated transaction and run-history endpoints.

## Technologies

| Layer | Stack |
| --- | --- |
| Frontend | Nuxt 4, Vue 3, TypeScript, Tailwind CSS 4, shadcn-vue, Nuxt UI |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, HTTPX |
| AI | TypeSafe Jev, OpenAI Responses API |
| Data | PostgreSQL 16, SQLite, Faker, JSON product catalogue |
| Tooling | Docker Compose, Adminer, pnpm, Make |

## Checks

```sh
make test   # Backend tests; no paid API calls
make check  # Backend tests, frontend type checking and production build
```
